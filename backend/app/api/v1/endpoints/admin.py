"""
Admin endpoints for financial summary and administrative functions
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.calculations import calculate_blended_cost_rate
from app.core.currency import normalize_to_primary_currency
from app.core.database import get_db
from app.core.money import Money
from app.core.permission_middleware import require_view_financial_projections
from app.core.tenant import TenantContext, get_tenant_context
from app.models.cost import CostFixed
from app.models.organization import Organization
from app.models.service import Service
from app.models.team import TeamMember
from app.models.user import User
from app.services.settings_service import SettingsService

router = APIRouter()


@router.get("/financial-summary")
async def get_financial_summary(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_financial_projections),
    db: AsyncSession = Depends(get_db),
):
    """
    Get financial summary for admin dashboard

    Returns:
    - monthlyFixedCosts: Total monthly fixed costs (rent, utilities, etc.)
    - monthlyPayroll: Total monthly payroll
    - totalBillableHours: Total billable hours capacity
    - blendedCostRate: Calculated BCR
    - activeTeamMembers: Number of active team members
    - currency: Primary currency

    **Permissions:**
    - Requires `can_view_financial_projections` permission
    """
    from app.core.cache import get_cache

    # Check cache
    cache = get_cache()
    cache_key = f"financial_summary:{tenant.organization_id}"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    # Get organization settings
    org_result = await db.execute(
        select(Organization).where(Organization.id == tenant.organization_id)
    )
    org = org_result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    settings_service = SettingsService(db)
    # Canonical currency source of truth for tenant financials
    primary_currency = await settings_service.get_primary_currency(tenant.organization_id)
    social_config = None
    if org.settings:
        social_config = org.settings.get("social_charges_config")

    # Calculate monthly fixed costs
    fixed_costs_query = select(CostFixed).where(
        CostFixed.organization_id == tenant.organization_id, CostFixed.deleted_at.is_(None)
    )
    fixed_costs_result = await db.execute(fixed_costs_query)
    fixed_costs = fixed_costs_result.scalars().all()

    monthly_fixed_costs = Decimal("0")
    for cost in fixed_costs:
        normalized = normalize_to_primary_currency(
            cost.amount_monthly, cost.currency or "USD", primary_currency
        )
        if isinstance(normalized, Money):
            normalized_decimal = normalized.amount
        else:
            normalized_decimal = Decimal(str(normalized))
        monthly_fixed_costs += normalized_decimal

    # Calculate monthly payroll
    team_members_query = select(TeamMember).where(
        TeamMember.organization_id == tenant.organization_id, TeamMember.is_active
    )
    team_members_result = await db.execute(team_members_query)
    team_members = team_members_result.scalars().all()

    monthly_payroll = Decimal("0")
    active_team_members = 0
    total_billable_hours = Decimal("0")

    for member in team_members:
        active_team_members += 1

        # Calculate monthly salary (normalize to primary currency)
        if member.salary_monthly_brute:
            normalized_salary = normalize_to_primary_currency(
                member.salary_monthly_brute, member.currency or "USD", primary_currency
            )
            if isinstance(normalized_salary, Money):
                monthly_payroll += normalized_salary.amount
            else:
                monthly_payroll += Decimal(str(normalized_salary))

        # Calculate billable hours (monthly capacity)
        if member.billable_hours_per_week:
            non_billable = Decimal(str(member.non_billable_hours_percentage or 0))
            monthly_hours = (
                Decimal(str(member.billable_hours_per_week))
                * Decimal("4.33")
                * (Decimal("1") - non_billable)
            )  # Average weeks per month adjusted by non billable ratio
            total_billable_hours += monthly_hours

    # Calculate blended cost rate
    blended_rate = await calculate_blended_cost_rate(
        db,
        primary_currency=primary_currency,
        tenant_id=tenant.organization_id,
        social_charges_config=social_config,
    )

    # Blended target margin = promedio del default_margin_target de los servicios
    # activos de la org (fallback 40%). Se usa para derivar la tasa de FACTURACIÓN
    # (precio/hora), que el break-even necesita — sin ella colapsa a margen cero.
    margins_result = await db.execute(
        select(Service.default_margin_target).where(
            Service.organization_id == tenant.organization_id,
            Service.is_active.is_(True),
            Service.deleted_at.is_(None),
        )
    )
    service_margins = [Decimal(str(m)) for (m,) in margins_result.all() if m is not None]
    if service_margins:
        blended_margin = sum(service_margins) / Decimal(len(service_margins))
    else:
        blended_margin = Decimal("0.40")
    # Clamp defensivo: margen en [0, 0.95) para evitar división por cero/negativa.
    if blended_margin < 0:
        blended_margin = Decimal("0")
    elif blended_margin >= Decimal("0.95"):
        blended_margin = Decimal("0.95")

    # Tasa de facturación blended: precio/hora = costo/hora / (1 - margen).
    # Misma convención de margen que el motor de cotización (Money.apply_margin).
    blended_bill_rate = blended_rate / (Decimal("1") - blended_margin)

    response = {
        "monthlyFixedCosts": float(monthly_fixed_costs),
        "monthlyPayroll": float(monthly_payroll),
        "totalBillableHours": float(total_billable_hours),
        "blendedCostRate": float(blended_rate),
        "blendedBillRate": float(blended_bill_rate),
        "targetMargin": float(blended_margin),
        "activeTeamMembers": active_team_members,
        "currency": primary_currency,
    }

    # Cache for 5 minutes
    cache.set(cache_key, response, ttl_seconds=300)

    return response
