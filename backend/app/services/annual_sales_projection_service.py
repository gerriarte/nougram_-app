"""
Service for calculating annual sales projection summaries
ESTÁNDAR NOUGRAM: Usa Decimal y Money para precisión monetaria
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.calculations import calculate_blended_cost_rate
from app.core.logging import get_logger
from app.core.money import Money
from app.models.annual_sales_projection import AnnualSalesProjection
from app.models.cost import CostFixed
from app.models.organization import Organization
from app.models.service import Service
from app.models.team import TeamMember

logger = get_logger(__name__)

# Month names in Spanish
MONTH_NAMES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]


async def calculate_projection_summary(projection: AnnualSalesProjection, db: AsyncSession) -> dict:
    """
    Calculate summary of annual sales projection

    Calculates:
    - Estimated revenue per month: quantity * hours_per_unit * (BCR * (1 + ServiceMargin))
    - Total annual projected revenue
    - Comparison with break-even (Overhead + Payroll monthly)

    Args:
        projection: AnnualSalesProjection instance
        db: Database session

    Returns:
        Dictionary with summary data including monthly breakdowns
    """
    # Get organization to get primary currency
    org_result = await db.execute(
        select(Organization).where(Organization.id == projection.organization_id)
    )
    org = org_result.scalar_one_or_none()

    if not org:
        raise ValueError(f"Organization {projection.organization_id} not found")

    primary_currency = org.settings.get("primary_currency", "USD") if org.settings else "USD"
    social_config = org.settings.get("social_charges_config") if org.settings else None

    # Get BCR (returns Decimal)
    bcr_decimal = await calculate_blended_cost_rate(
        db,
        primary_currency=primary_currency,
        use_cache=True,
        tenant_id=projection.organization_id,
        social_charges_config=social_config,
    )
    bcr_money = Money(bcr_decimal, primary_currency)

    # Get all services referenced in entries
    service_ids = {entry.service_id for entry in projection.entries}
    if not service_ids:
        # No entries, return empty summary
        return {
            "summary": [],
            "total_annual_revenue": Decimal("0"),
            "total_annual_hours": 0.0,
            "break_even_monthly_cost": Decimal("0"),
        }

    services_result = await db.execute(
        select(Service).where(
            Service.id.in_(service_ids), Service.organization_id == projection.organization_id
        )
    )
    services = {service.id: service for service in services_result.scalars().all()}

    # Calculate break-even monthly cost (Overhead + Payroll)
    # Get fixed costs
    costs_result = await db.execute(
        select(CostFixed).where(
            CostFixed.organization_id == projection.organization_id, CostFixed.deleted_at.is_(None)
        )
    )
    fixed_costs = costs_result.scalars().all()

    # Get team members
    team_result = await db.execute(
        select(TeamMember).where(
            TeamMember.organization_id == projection.organization_id, TeamMember.is_active
        )
    )
    team_members = team_result.scalars().all()

    # Calculate total monthly costs (fixed + salaries with social charges)
    # ESTÁNDAR NOUGRAM: Usar Money para todos los cálculos
    from app.core.currency import normalize_to_primary_currency

    total_monthly_cost_money = Money(Decimal("0"), primary_currency)

    # Add fixed costs
    for cost in fixed_costs:
        cost_currency = cost.currency or "USD"
        cost_money = Money(cost.amount_monthly, cost_currency)
        normalized = normalize_to_primary_currency(cost_money, cost_currency, primary_currency)
        # normalize_to_primary_currency retorna Money si input es Money
        if isinstance(normalized, Money):
            total_monthly_cost_money = total_monthly_cost_money.add(normalized)
        else:
            # Compatibilidad hacia atrás: convertir float a Money
            total_monthly_cost_money = total_monthly_cost_money.add(
                Money(normalized, primary_currency)
            )

    # Add salaries with social charges
    if social_config and social_config.get("enable_social_charges", False):
        total_percentage = social_config.get("total_percentage", 0)
        social_charges_multiplier = Decimal("1") + (Decimal(str(total_percentage)) / Decimal("100"))
    else:
        social_charges_multiplier = Decimal("1")

    for member in team_members:
        member_currency = member.currency or "USD"
        salary_money = Money(member.salary_monthly_brute, member_currency)
        normalized = normalize_to_primary_currency(salary_money, member_currency, primary_currency)
        # normalize_to_primary_currency retorna Money si input es Money
        effective_mult = (
            social_charges_multiplier
            if getattr(member, "apply_social_charges", True)
            else Decimal("1")
        )
        if isinstance(normalized, Money):
            salary_with_charges = normalized.multiply(effective_mult)
        else:
            salary_with_charges = Money(normalized, primary_currency).multiply(effective_mult)
        total_monthly_cost_money = total_monthly_cost_money.add(salary_with_charges)

    break_even_monthly_cost = total_monthly_cost_money.amount

    # Initialize monthly summaries
    monthly_summaries = {}
    for month in range(1, 13):
        monthly_summaries[month] = {
            "month": month,
            "month_name": MONTH_NAMES[month - 1],
            "total_revenue": Decimal("0"),
            "total_hours": 0.0,
            "service_breakdown": [],
        }

    # Process each entry
    for entry in projection.entries:
        service = services.get(entry.service_id)
        if not service:
            logger.warning(f"Service {entry.service_id} not found for entry {entry.id}")
            continue

        # Get service margin target (default 0.40 = 40%)
        margin_target = service.default_margin_target or Decimal("0.40")

        # Calculate revenue for this entry
        # Revenue = quantity * hours_per_unit * (BCR * (1 + margin_target))
        # ESTÁNDAR NOUGRAM: Usar Decimal para todos los cálculos
        total_hours = Decimal(str(entry.quantity)) * Decimal(str(entry.hours_per_unit))
        cost_money = bcr_money.multiply(total_hours)
        margin_multiplier = Decimal("1") + margin_target
        revenue_money = cost_money.multiply(margin_multiplier)

        month = entry.month
        if month not in monthly_summaries:
            continue

        # Add to monthly summary
        monthly_summaries[month]["total_revenue"] += revenue_money.amount
        monthly_summaries[month]["total_hours"] += float(total_hours)

        # Add to service breakdown
        monthly_summaries[month]["service_breakdown"].append(
            {
                "service_id": service.id,
                "service_name": service.name,
                "quantity": entry.quantity,
                "hours_per_unit": entry.hours_per_unit,
                "total_hours": float(total_hours),
                "revenue": str(revenue_money.amount),
            }
        )

    # Convert to list format
    summary_list = [monthly_summaries[month] for month in range(1, 13)]

    # Calculate totals
    total_annual_revenue = sum(Decimal(str(s["total_revenue"])) for s in summary_list)
    total_annual_hours = sum(s["total_hours"] for s in summary_list)

    return {
        "summary": summary_list,
        "total_annual_revenue": total_annual_revenue,
        "total_annual_hours": total_annual_hours,
        "break_even_monthly_cost": break_even_monthly_cost,
    }
