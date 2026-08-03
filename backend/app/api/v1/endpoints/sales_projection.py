"""
Sales projection endpoints (Sprint 18)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.currency import is_valid_currency, resolve_primary_currency
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant_context
from app.models.organization import Organization
from app.models.user import User
from app.services.sales_projection_service import calculate_sales_projection

logger = get_logger(__name__)
router = APIRouter()


def resolve_projection_currency(org: Organization | None, requested: str | None) -> str:
    """
    Currency the projection must be computed in: always the organization's primary.

    `currency` used to come straight from the request body with a "USD" default and
    no validation, and it is not a display label: it is the TARGET of the cost
    normalization inside calculate_blended_cost_rate, so an org running on COP got
    every cost divided by the COP rate and a BCR ~4000x too low, reported back as
    dollars. The client may still send it, but only to confirm the org's own
    currency; anything else is rejected instead of answering a plausible wrong number.

    Raises:
        ValueError: if `requested` is not a supported code or disagrees with the org.
    """
    primary_currency = resolve_primary_currency(org)
    if requested is None:
        return primary_currency

    normalized = str(requested).strip().upper()
    if not is_valid_currency(normalized):
        raise ValueError(f"Unsupported currency '{requested}'")
    if normalized != primary_currency:
        raise ValueError(
            f"Currency '{normalized}' does not match the organization's primary currency "
            f"'{primary_currency}'. Projections are always calculated in the primary currency."
        )
    return primary_currency


class SalesProjectionRequest(BaseModel):
    """Request schema for sales projection"""

    service_ids: list[int] = Field(..., description="List of service IDs to project", min_items=1)
    estimated_hours_per_service: dict[int, float] = Field(
        ...,
        description="Dictionary mapping service_id to estimated hours",
        example={1: 40.0, 2: 20.0},
    )
    win_rate: float = Field(0.85, ge=0.0, le=1.0, description="Expected win rate (0.0 to 1.0)")
    scenario: str = Field(
        "realistic", description="Scenario type: conservative, realistic, optimistic"
    )
    period_months: int = Field(12, ge=1, le=36, description="Number of months to project")
    currency: str | None = Field(
        None,
        description=(
            "Optional. Must match the organization's primary currency; when omitted "
            "the primary currency is used. It is NOT a display-only label."
        ),
    )

    class Config:
        json_schema_extra = {
            "example": {
                "service_ids": [1, 2, 3],
                "estimated_hours_per_service": {"1": 40.0, "2": 20.0, "3": 60.0},
                "win_rate": 0.85,
                "scenario": "realistic",
                "period_months": 12,
            }
        }


@router.post("/projection", summary="Calculate sales projection")
async def create_sales_projection(
    projection_data: SalesProjectionRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate sales projection based on services, team capacity, and win rates.

    **Permissions:**
    - All authenticated users can calculate projections for their organization

    **Request Body:**
    - `service_ids`: List of service IDs to include in projection
    - `estimated_hours_per_service`: Dictionary mapping service_id to estimated hours
    - `win_rate`: Expected win rate (0.0 to 1.0, default 0.85)
    - `scenario`: Scenario type ("conservative", "realistic", "optimistic")
    - `period_months`: Number of months to project (1-36, default 12)
    - `currency`: Optional; must match the organization's primary currency (400 otherwise).
      Omit it to use the primary currency, which is what the calculation always uses.

    **Returns:**
    - `200 OK`: Projection calculated successfully
    - `400 Bad Request`: Invalid input data
    - `404 Not Found`: Services not found

    **Response includes:**
    - Service-level projections (revenue, costs, profit per service)
    - Monthly breakdown (revenue, costs, profit per month)
    - Summary KPIs (total revenue, costs, profit, margin, capacity utilization)
    """
    org_result = await db.execute(
        select(Organization).where(Organization.id == tenant.organization_id)
    )
    organization = org_result.scalar_one_or_none()
    try:
        effective_currency = resolve_projection_currency(organization, projection_data.currency)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    try:
        projection = await calculate_sales_projection(
            db=db,
            organization_id=tenant.organization_id,
            service_ids=projection_data.service_ids,
            estimated_hours_per_service={
                int(k): float(v) for k, v in projection_data.estimated_hours_per_service.items()
            },
            win_rate=projection_data.win_rate,
            scenario=projection_data.scenario,
            period_months=projection_data.period_months,
            currency=effective_currency,
        )

        logger.info(
            f"Sales projection calculated for organization {tenant.organization_id} by user {current_user.id}",
            scenario=projection_data.scenario,
            period_months=projection_data.period_months,
        )

        return projection

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error calculating sales projection for organization {tenant.organization_id}",
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error calculating sales projection",
        )
