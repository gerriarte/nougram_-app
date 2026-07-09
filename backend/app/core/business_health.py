"""
Business-health analytics: monthly operating cost, break-even point and resource
utilization for approved (Won) projects.

Net-new analytics that build on the existing BCR cost basis. The monthly operating
cost replicates the same aggregation used by `calculate_blended_cost_rate`
(fixed costs + equipment amortization + payroll with social charges) so the
break-even figure is consistent with the BCR.
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.currency import normalize_to_primary_currency
from app.core.logging import get_logger
from app.core.money import Money, sum_money
from app.models.cost import CostFixed
from app.models.equipment import EquipmentAmortization
from app.models.team import TeamMember

logger = get_logger(__name__)


async def _social_charges_multiplier(
    db: AsyncSession,
    tenant_id: int | None,
    social_charges_config: dict | None = None,
) -> Decimal:
    """1 + (sum of social-charge percentages / 100). Reads org settings, else the passed config."""
    social_config = None
    if tenant_id is not None:
        try:
            from app.models.organization import Organization

            org_result = await db.execute(select(Organization).where(Organization.id == tenant_id))
            org = org_result.scalar_one_or_none()
            if org and org.settings and org.settings.get("social_charges_config"):
                social_config = org.settings.get("social_charges_config", {})
        except Exception as e:  # pragma: no cover - defensive
            logger.warning(f"Error getting social charges config: {e}")
            social_config = None

    if social_config is None:
        social_config = social_charges_config or {}

    if not social_config.get("enable_social_charges", False):
        return Decimal("1.0")

    components = [
        "health_percentage",
        "pension_percentage",
        "arl_percentage",
        "parafiscales_percentage",
        "prima_services_percentage",
        "cesantias_percentage",
        "int_cesantias_percentage",
        "vacations_percentage",
    ]
    total_percentage = Decimal("0")
    for key in components:
        total_percentage += Decimal(str(social_config.get(key, 0) or 0))
    if total_percentage == 0:
        total_percentage = Decimal(str(social_config.get("total_percentage", 0) or 0))

    if total_percentage > 0:
        return Decimal("1") + (total_percentage / Decimal("100"))
    return Decimal("1.0")


async def calculate_monthly_operating_cost(
    db: AsyncSession,
    primary_currency: str = "USD",
    tenant_id: int | None = None,
    social_charges_config: dict | None = None,
) -> dict:
    """
    Monthly operating cost and billable capacity. Mirrors the BCR basis:
    fixed costs + equipment amortization + payroll (with social charges).
    """
    # Fixed costs
    query = select(CostFixed).where(CostFixed.deleted_at.is_(None))
    if tenant_id is not None:
        query = query.where(CostFixed.organization_id == tenant_id)
    fixed_costs = (await db.execute(query)).scalars().all()
    fixed_money = []
    for cost in fixed_costs:
        normalized = normalize_to_primary_currency(
            Decimal(str(cost.amount_monthly)), cost.currency or "USD", primary_currency
        )
        fixed_money.append(
            normalized if isinstance(normalized, Money) else Money(normalized, primary_currency)
        )
    total_fixed = (sum_money(fixed_money) or Money(0, primary_currency)).amount

    # Equipment amortization (monthly depreciation)
    eq_query = select(EquipmentAmortization).where(
        EquipmentAmortization.deleted_at.is_(None), EquipmentAmortization.is_active
    )
    if tenant_id is not None:
        eq_query = eq_query.where(EquipmentAmortization.organization_id == tenant_id)
    equipment = (await db.execute(eq_query)).scalars().all()
    eq_money = []
    for asset in equipment:
        useful_life = int(asset.useful_life_months or 0)
        if useful_life <= 0:
            continue
        monthly_dep = (
            Decimal(str(asset.purchase_price or 0)) - Decimal(str(asset.salvage_value or 0))
        ) / Decimal(str(useful_life))
        if monthly_dep <= 0:
            continue
        normalized = normalize_to_primary_currency(
            monthly_dep, asset.currency or "USD", primary_currency
        )
        eq_money.append(
            normalized if isinstance(normalized, Money) else Money(normalized, primary_currency)
        )
    total_equipment = (sum_money(eq_money) or Money(0, primary_currency)).amount

    # Payroll with social charges (respecting per-member apply_social_charges flag)
    query = select(TeamMember).where(TeamMember.is_active)
    if tenant_id is not None:
        query = query.where(TeamMember.organization_id == tenant_id)
    members = (await db.execute(query)).scalars().all()
    multiplier = await _social_charges_multiplier(db, tenant_id, social_charges_config)
    salary_money = []
    billable_hours = Decimal("0")
    for member in members:
        normalized = normalize_to_primary_currency(
            member.salary_monthly_brute, member.currency or "USD", primary_currency
        )
        money = normalized if isinstance(normalized, Money) else Money(normalized, primary_currency)
        effective_mult = (
            multiplier if getattr(member, "apply_social_charges", True) else Decimal("1")
        )
        salary_money.append(money.multiply(effective_mult))
        non_billable = getattr(member, "non_billable_hours_percentage", 0.0) or 0.0
        billable_hours += (
            Decimal(str(member.billable_hours_per_week))
            * Decimal("4.33")
            * (Decimal("1") - Decimal(str(non_billable)))
        )
    total_payroll = (sum_money(salary_money) or Money(0, primary_currency)).amount

    total_monthly_cost = total_fixed + total_equipment + total_payroll

    return {
        "total_fixed": total_fixed,
        "total_equipment": total_equipment,
        "total_payroll": total_payroll,
        "total_monthly_cost": total_monthly_cost,
        "billable_hours": billable_hours,
        "active_team_members": len(members),
        "currency": primary_currency,
    }


async def _accepted_quote_ids(db: AsyncSession, tenant_id: int) -> list[int]:
    """Quote id considered accepted for each Won project (accepted_quote_id, else latest version)."""
    from app.models.project import Project, Quote

    result = await db.execute(
        select(Project).where(
            Project.organization_id == tenant_id,
            Project.status == "Won",
            Project.deleted_at.is_(None),
        )
    )
    projects = result.scalars().all()
    quote_ids: list[int] = []
    for project in projects:
        accepted_id = getattr(project, "accepted_quote_id", None)
        if accepted_id:
            quote_ids.append(accepted_id)
            continue
        latest = await db.execute(
            select(Quote.id)
            .where(Quote.project_id == project.id)
            .order_by(Quote.version.desc())
            .limit(1)
        )
        latest_id = latest.scalar_one_or_none()
        if latest_id:
            quote_ids.append(latest_id)
    return quote_ids


async def calculate_committed_monthly_revenue(
    db: AsyncSession,
    tenant_id: int,
    primary_currency: str = "USD",
    one_time_proration_months: int = 12,
) -> dict:
    """Monthly committed revenue from Won projects: MRR (recurring) + prorated one-time."""
    from app.models.project import QuoteItem

    quote_ids = await _accepted_quote_ids(db, tenant_id)
    mrr = Money(0, primary_currency)
    one_time = Money(0, primary_currency)

    if quote_ids:
        items = (
            (await db.execute(select(QuoteItem).where(QuoteItem.quote_id.in_(quote_ids))))
            .scalars()
            .all()
        )
        for item in items:
            pricing_type = item.pricing_type or "hourly"
            if pricing_type == "recurring":
                monthly = Decimal(str(item.recurring_price or 0)) * Decimal(str(item.quantity or 1))
                if (item.billing_frequency or "monthly") == "annual":
                    monthly = monthly / Decimal("12")
                mrr = mrr.add(Money(monthly, primary_currency))
            else:
                one_time = one_time.add(
                    Money(Decimal(str(item.client_price or 0)), primary_currency)
                )

    proration = (
        Decimal(str(one_time_proration_months))
        if one_time_proration_months and one_time_proration_months > 0
        else Decimal("1")
    )
    one_time_monthly = one_time.amount / proration
    committed = mrr.amount + one_time_monthly

    return {
        "mrr": mrr.amount,
        "one_time_monthly": one_time_monthly,
        "committed_monthly_revenue": committed,
        "currency": primary_currency,
    }


async def calculate_break_even(
    db: AsyncSession,
    tenant_id: int,
    primary_currency: str = "USD",
    social_charges_config: dict | None = None,
    one_time_proration_months: int = 12,
) -> dict:
    """Monthly break-even: operating cost vs committed revenue."""
    operating = await calculate_monthly_operating_cost(
        db,
        primary_currency=primary_currency,
        tenant_id=tenant_id,
        social_charges_config=social_charges_config,
    )
    revenue = await calculate_committed_monthly_revenue(
        db,
        tenant_id=tenant_id,
        primary_currency=primary_currency,
        one_time_proration_months=one_time_proration_months,
    )

    break_even_cost = operating["total_monthly_cost"]
    committed = revenue["committed_monthly_revenue"]
    capacity_hours = operating["billable_hours"]
    surplus = committed - break_even_cost

    coverage_pct = float(committed / break_even_cost) if break_even_cost > 0 else 0.0
    break_even_rate_per_hour = (
        float(break_even_cost / capacity_hours) if capacity_hours > 0 else 0.0
    )
    status = "profit" if surplus > 0 else ("break_even" if surplus == 0 else "deficit")

    return {
        "currency": primary_currency,
        "break_even_cost": float(break_even_cost),
        "total_fixed": float(operating["total_fixed"]),
        "total_equipment": float(operating["total_equipment"]),
        "total_payroll": float(operating["total_payroll"]),
        "committed_revenue": float(committed),
        "mrr": float(revenue["mrr"]),
        "one_time_monthly": float(revenue["one_time_monthly"]),
        "coverage_percentage": coverage_pct,
        "surplus_or_deficit": float(surplus),
        "break_even_rate_per_hour": break_even_rate_per_hour,
        "capacity_hours": float(capacity_hours),
        "active_team_members": operating["active_team_members"],
        "status": status,
    }


def _as_naive(dt):
    if dt is not None and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def _periods_overlap(a_start, a_end, b_start, b_end) -> bool:
    a_start, a_end = _as_naive(a_start), _as_naive(a_end)
    b_start, b_end = _as_naive(b_start), _as_naive(b_end)
    if b_start is not None and a_end is not None and a_end < b_start:
        return False
    if b_end is not None and a_start is not None and a_start > b_end:
        return False
    return True


async def calculate_resource_utilization(
    db: AsyncSession,
    tenant_id: int,
    start=None,
    end=None,
) -> dict:
    """Allocated hours per member across accepted quotes of Won projects vs monthly capacity."""
    from app.models.project import QuoteItem, QuoteItemAllocation

    quote_ids = await _accepted_quote_ids(db, tenant_id)
    allocated: dict[int, Decimal] = {}
    if quote_ids:
        allocations = (
            (
                await db.execute(
                    select(QuoteItemAllocation)
                    .join(QuoteItem, QuoteItemAllocation.quote_item_id == QuoteItem.id)
                    .where(QuoteItem.quote_id.in_(quote_ids))
                )
            )
            .scalars()
            .all()
        )
        for alloc in allocations:
            if (start is not None or end is not None) and not _periods_overlap(
                alloc.start_date, alloc.end_date, start, end
            ):
                continue
            allocated[alloc.team_member_id] = allocated.get(
                alloc.team_member_id, Decimal("0")
            ) + Decimal(str(alloc.hours or 0))

    members = (
        (
            await db.execute(
                select(TeamMember).where(
                    TeamMember.is_active, TeamMember.organization_id == tenant_id
                )
            )
        )
        .scalars()
        .all()
    )

    members_out = []
    total_capacity = Decimal("0")
    total_allocated = Decimal("0")
    for member in members:
        non_billable = getattr(member, "non_billable_hours_percentage", 0.0) or 0.0
        capacity = (
            Decimal(str(member.billable_hours_per_week))
            * Decimal("4.33")
            * (Decimal("1") - Decimal(str(non_billable)))
        )
        used = allocated.get(member.id, Decimal("0"))
        total_capacity += capacity
        total_allocated += used
        members_out.append(
            {
                "team_member_id": member.id,
                "name": member.name,
                "role": member.role,
                "capacity_hours": float(capacity),
                "allocated_hours": float(used),
                "remaining_hours": float(capacity - used),
                "utilization_percentage": float(used / capacity * 100) if capacity > 0 else 0.0,
                "over_allocated": used > capacity,
            }
        )

    overall = float(total_allocated / total_capacity * 100) if total_capacity > 0 else 0.0
    return {
        "members": members_out,
        "total_capacity_hours": float(total_capacity),
        "total_allocated_hours": float(total_allocated),
        "overall_utilization_percentage": overall,
    }
