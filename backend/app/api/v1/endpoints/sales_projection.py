"""
Sales projection endpoints (Sprint 18)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant_context
from app.models.user import User
from app.services.sales_projection_service import calculate_sales_projection

logger = get_logger(__name__)
router = APIRouter()


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
    currency: str = Field("USD", description="Currency for calculations")

    class Config:
        json_schema_extra = {
            "example": {
                "service_ids": [1, 2, 3],
                "estimated_hours_per_service": {"1": 40.0, "2": 20.0, "3": 60.0},
                "win_rate": 0.85,
                "scenario": "realistic",
                "period_months": 12,
                "currency": "USD",
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
    - `currency`: Currency for calculations (default "USD")

    **Returns:**
    - `200 OK`: Projection calculated successfully
    - `400 Bad Request`: Invalid input data
    - `404 Not Found`: Services not found

    **Response includes:**
    - Service-level projections (revenue, costs, profit per service)
    - Monthly breakdown (revenue, costs, profit per month)
    - Summary KPIs (total revenue, costs, profit, margin, capacity utilization)
    """
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
            currency=projection_data.currency,
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
