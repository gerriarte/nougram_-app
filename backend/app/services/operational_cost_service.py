"""
Operational cost calculation service — single source of truth for monthly operational metrics.
ESTÁNDAR NOUGRAM: Decimal end-to-end; structured logging with calculation_id for traceability.
"""

from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.currency import normalize_to_primary_currency
from app.core.exceptions import BusinessLogicError
from app.core.logging import get_logger
from app.core.money import Money
from app.models.cost import CostFixed
from app.models.equipment import EquipmentAmortization
from app.models.organization import Organization
from app.models.project import Project, Quote, project_taxes
from app.models.service import Service
from app.models.tax import Tax
from app.models.team import TeamMember
from app.schemas.operational_cost import (
    CalculationMetadataSchema,
    OperationalCostPayloadSchema,
)

logger = get_logger(__name__)

FORMULA_VERSION = "1.0"


async def get_current_month_operational_costs(
    db: AsyncSession,
    organization_id: int,
    primary_currency: str = "USD",
    period_start: date | None = None,
    period_end: date | None = None,
) -> OperationalCostPayloadSchema:
    """
    Compute canonical operational cost payload for the given organization and period.
    Default period is current month. All amounts in primary_currency, Decimal.
    """
    today = date.today()
    if period_start is None:
        period_start = today.replace(day=1)
    if period_end is None:
        period_end = today

    calculation_id = str(uuid4())
    logger.info(
        "Computing operational costs",
        extra={
            "context": {
                "module": "operational_cost_service",
                "function": "get_current_month_operational_costs",
                "calculation_id": calculation_id,
                "organization_id": organization_id,
                "period_start": str(period_start),
                "period_end": str(period_end),
                "currency": primary_currency,
            }
        },
    )

    # 1. Resource costs (payroll + social charges)
    resource_costs = await _compute_resource_costs(
        db, organization_id, primary_currency, calculation_id
    )

    # 2. Fixed costs (overhead, excl. amortization)
    fixed_costs = await _compute_fixed_costs(db, organization_id, primary_currency, calculation_id)

    # 3. Amortization (monthly depreciation)
    amortization, amortization_ok = await _compute_amortization(
        db, organization_id, primary_currency, calculation_id
    )

    # 4. Tax costs (operational tax burden if any; e.g. withholdings)
    tax_costs = await _compute_tax_costs(
        db,
        organization_id,
        primary_currency,
        calculation_id,
        period_start=period_start,
        period_end=period_end,
        operational_subtotal=resource_costs + fixed_costs + amortization,
    )

    total_operational_cost = resource_costs + fixed_costs + amortization + tax_costs

    # 5. Target margin (from org settings or average service default)
    target_margin = await _get_target_margin_configured(db, organization_id, calculation_id)

    # 6. Effective margin (from Won quotes in period)
    effective_margin = await _get_effective_margin_observed(
        db, organization_id, period_start, period_end, primary_currency, calculation_id
    )

    data_integrity_ok = amortization_ok  # Can extend with more checks

    metadata = CalculationMetadataSchema(
        currency=primary_currency,
        period_start=period_start,
        period_end=period_end,
        formula_version=FORMULA_VERSION,
        calculation_id=calculation_id,
    )

    payload = OperationalCostPayloadSchema(
        resource_costs=resource_costs,
        fixed_costs=fixed_costs,
        amortization=amortization,
        tax_costs=tax_costs,
        total_operational_cost=total_operational_cost,
        target_margin_configured=target_margin,
        effective_margin_observed=effective_margin,
        calculation_metadata=metadata,
        data_integrity_ok=data_integrity_ok,
    )

    logger.info(
        "Operational costs computed",
        extra={
            "context": {
                "module": "operational_cost_service",
                "function": "get_current_month_operational_costs",
                "calculation_id": calculation_id,
                "total_operational_cost": str(total_operational_cost),
            }
        },
    )
    return payload


def _to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


async def _get_social_charges_multiplier(db: AsyncSession, organization_id: int) -> Decimal:
    """Return 1 + (total_percentage/100) from org social_charges_config, or 1.0."""
    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    org = result.scalar_one_or_none()
    if not org or not org.settings or not org.settings.get("social_charges_config"):
        return Decimal("1.0")
    cfg = org.settings.get("social_charges_config", {})
    if not cfg.get("enable_social_charges", False):
        return Decimal("1.0")
    total = Decimal("0")
    total += Decimal(str(cfg.get("health_percentage", 0) or 0))
    total += Decimal(str(cfg.get("pension_percentage", 0) or 0))
    total += Decimal(str(cfg.get("arl_percentage", 0) or 0))
    total += Decimal(str(cfg.get("parafiscales_percentage", 0) or 0))
    total += Decimal(str(cfg.get("prima_services_percentage", 0) or 0))
    total += Decimal(str(cfg.get("cesantias_percentage", 0) or 0))
    total += Decimal(str(cfg.get("int_cesantias_percentage", 0) or 0))
    total += Decimal(str(cfg.get("vacations_percentage", 0) or 0))
    if total == 0:
        total = Decimal(str(cfg.get("total_percentage", 0) or 0))
    return Decimal("1") + (total / Decimal("100"))


async def _compute_resource_costs(
    db: AsyncSession,
    organization_id: int,
    primary_currency: str,
    calculation_id: str,
) -> Decimal:
    """Total monthly resource cost (salaries + social charges) in primary currency."""
    multiplier = await _get_social_charges_multiplier(db, organization_id)
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.is_active,
            TeamMember.organization_id == organization_id,
        )
    )
    members = result.scalars().all()
    total = Decimal("0")
    for member in members:
        amt = _to_decimal(member.salary_monthly_brute)
        if amt < 0:
            raise BusinessLogicError(
                f"Invalid negative salary for team member {member.id} in organization {organization_id}"
            )
        cur = member.currency or "USD"
        norm = normalize_to_primary_currency(amt, cur, primary_currency)
        if isinstance(norm, Money):
            dec = norm.amount
        else:
            dec = Decimal(str(norm))
        effective = multiplier if getattr(member, "apply_social_charges", True) else Decimal("1")
        total += (dec * effective).quantize(Decimal("0.0001"))
    return total


async def _compute_fixed_costs(
    db: AsyncSession,
    organization_id: int,
    primary_currency: str,
    calculation_id: str,
) -> Decimal:
    """Fixed/overhead costs (excl. amortization) in primary currency."""
    result = await db.execute(
        select(CostFixed).where(
            CostFixed.deleted_at.is_(None),
            CostFixed.organization_id == organization_id,
        )
    )
    costs = result.scalars().all()
    total = Decimal("0")
    for cost in costs:
        amt = _to_decimal(cost.amount_monthly)
        if amt < 0:
            raise BusinessLogicError(
                f"Invalid negative fixed cost {cost.id} in organization {organization_id}"
            )
        cur = cost.currency or "USD"
        norm = normalize_to_primary_currency(amt, cur, primary_currency)
        if isinstance(norm, Money):
            total += norm.amount
        else:
            total += Decimal(str(norm))
    return total.quantize(Decimal("0.0001"))


async def _compute_amortization(
    db: AsyncSession,
    organization_id: int,
    primary_currency: str,
    calculation_id: str,
) -> tuple[Decimal, bool]:
    """Monthly depreciation total in primary currency. Second return is data_integrity_ok for this block."""
    result = await db.execute(
        select(EquipmentAmortization).where(
            EquipmentAmortization.deleted_at.is_(None),
            EquipmentAmortization.is_active,
            EquipmentAmortization.organization_id == organization_id,
        )
    )
    assets = result.scalars().all()
    total = Decimal("0")
    integrity_ok = True
    for asset in assets:
        life = int(asset.useful_life_months or 0)
        if life <= 0:
            integrity_ok = False
            continue
        purchase = _to_decimal(asset.purchase_price or 0)
        salvage = _to_decimal(asset.salvage_value or 0)
        if purchase < 0 or salvage < 0:
            raise BusinessLogicError(
                f"Invalid negative amortization values for asset {asset.id} in organization {organization_id}"
            )
        if salvage > purchase:
            raise BusinessLogicError(
                f"Invalid amortization values for asset {asset.id}: salvage value cannot exceed purchase price"
            )
        monthly = (purchase - salvage) / Decimal(str(life))
        if monthly <= 0:
            integrity_ok = False
            continue
        cur = asset.currency or "USD"
        norm = normalize_to_primary_currency(monthly, cur, primary_currency)
        if isinstance(norm, Money):
            total += norm.amount
        else:
            total += Decimal(str(norm))
    # Fallback for organizations that still have onboarding inventory in settings
    # but no persisted EquipmentAmortization rows yet.
    if total == 0:
        settings_fallback = await _compute_amortization_from_onboarding_settings(
            db=db,
            organization_id=organization_id,
            primary_currency=primary_currency,
        )
        total += settings_fallback

    return total.quantize(Decimal("0.0001")), integrity_ok


async def _compute_amortization_from_onboarding_settings(
    db: AsyncSession,
    organization_id: int,
    primary_currency: str,
) -> Decimal:
    """Legacy-safe fallback: derive monthly amortization from onboarding inventory settings."""
    org_result = await db.execute(select(Organization).where(Organization.id == organization_id))
    org = org_result.scalar_one_or_none()
    if not org or not org.settings:
        return Decimal("0")

    inventory_items = org.settings.get("onboarding_inventory_items") or []
    total = Decimal("0")
    for item in inventory_items:
        try:
            if not bool(item.get("amortizable")):
                continue
            amount = Decimal(str(item.get("amount_monthly") or "0"))
            if amount <= 0:
                continue
            category = str(item.get("category") or "").lower()
            useful_life_months = Decimal("24") if category == "software" else Decimal("36")
            monthly = amount / useful_life_months
            item_currency = str(item.get("currency") or primary_currency or "USD")
            normalized = normalize_to_primary_currency(monthly, item_currency, primary_currency)
            if isinstance(normalized, Money):
                total += normalized.amount
            else:
                total += Decimal(str(normalized))
        except Exception:
            # Keep fallback resilient to malformed legacy entries.
            continue
    return total.quantize(Decimal("0.0001"))


async def _compute_tax_costs(
    db: AsyncSession,
    organization_id: int,
    primary_currency: str,
    calculation_id: str,
    period_start: date,
    period_end: date,
    operational_subtotal: Decimal,
) -> Decimal:
    """
    Operational tax cost for the period based on taxes attached to Won projects.
    For each quote in period, computes tax amount from project tax percentages.
    """
    from datetime import datetime

    start_dt = datetime.combine(period_start, datetime.min.time())
    end_dt = datetime.combine(period_end, datetime.max.time())

    rows_result = await db.execute(
        select(
            Quote.total_client_price,
            Project.currency,
            Tax.percentage,
        )
        .join(Project, Quote.project_id == Project.id)
        .join(project_taxes, project_taxes.c.project_id == Project.id)
        .join(Tax, Tax.id == project_taxes.c.tax_id)
        .where(
            Project.organization_id == organization_id,
            Project.deleted_at.is_(None),
            Project.status == "Won",
            func.coalesce(Quote.updated_at, Quote.created_at) >= start_dt,
            func.coalesce(Quote.updated_at, Quote.created_at) <= end_dt,
            Tax.is_active,
            Tax.deleted_at.is_(None),
        )
    )
    rows = rows_result.all()
    total = Decimal("0")
    for total_client_price, project_currency, tax_percentage in rows:
        price = _to_decimal(total_client_price)
        percentage = _to_decimal(tax_percentage)
        if percentage < 0:
            raise BusinessLogicError(
                f"Invalid negative tax percentage in organization {organization_id}"
            )
        tax_amount = price * (percentage / Decimal("100"))
        normalized = normalize_to_primary_currency(
            tax_amount,
            project_currency or "USD",
            primary_currency,
        )
        if isinstance(normalized, Money):
            total += normalized.amount
        else:
            total += Decimal(str(normalized))
    # If there are no Won quotes in period but taxes are configured, apply current
    # active taxes to current operational subtotal as canonical monthly applicable tax burden.
    if total == 0 and operational_subtotal > 0:
        configured_taxes_result = await db.execute(
            select(Tax.percentage).where(
                Tax.organization_id == organization_id,
                Tax.is_active,
                Tax.deleted_at.is_(None),
            )
        )
        configured_taxes = configured_taxes_result.scalars().all()
        configured_total = Decimal("0")
        for percentage_raw in configured_taxes:
            percentage = _to_decimal(percentage_raw)
            if percentage < 0:
                raise BusinessLogicError(
                    f"Invalid negative tax percentage in organization {organization_id}"
                )
            configured_total += operational_subtotal * (percentage / Decimal("100"))
        total += configured_total

    return total.quantize(Decimal("0.0001"))


async def _get_target_margin_configured(
    db: AsyncSession, organization_id: int, calculation_id: str
) -> Decimal | None:
    """Target margin used when quoting: from org.settings.quote_default_margin or average of services."""
    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    org = result.scalar_one_or_none()
    if org and org.settings and org.settings.get("quote_default_margin") is not None:
        val = org.settings.get("quote_default_margin")
        return Decimal(str(val)).quantize(Decimal("0.0001"))
    # Fallback: average default_margin_target of active services
    r = await db.execute(
        select(func.avg(Service.default_margin_target)).where(
            Service.organization_id == organization_id,
            Service.deleted_at.is_(None),
            Service.is_active,
        )
    )
    avg = r.scalar()
    if avg is None:
        return None
    return Decimal(str(avg)).quantize(Decimal("0.0001"))


async def _get_effective_margin_observed(
    db: AsyncSession,
    organization_id: int,
    period_start: date,
    period_end: date,
    primary_currency: str,
    calculation_id: str,
) -> Decimal | None:
    """Effective margin from Won projects in period: (revenue - cost) / revenue. Revenue/cost in project currency, then we use as-is for ratio."""
    from datetime import datetime

    start_dt = datetime.combine(period_start, datetime.min.time())
    end_dt = datetime.combine(period_end, datetime.max.time())

    # Quotes that belong to Won projects and were updated in period (or project updated in period)
    subq = (
        select(
            Quote.id,
            Quote.total_client_price,
            Quote.total_internal_cost,
            Project.currency,
        )
        .join(Project, Quote.project_id == Project.id)
        .where(
            Project.organization_id == organization_id,
            Project.deleted_at.is_(None),
            Project.status == "Won",
            func.coalesce(Quote.updated_at, Quote.created_at) >= start_dt,
            func.coalesce(Quote.updated_at, Quote.created_at) <= end_dt,
        )
    )
    result = await db.execute(subq)
    rows = result.all()
    sum_price = Decimal("0")
    sum_cost = Decimal("0")
    for row in rows:
        project_currency = row.currency or "USD"
        price = _to_decimal(row.total_client_price)
        cost = _to_decimal(row.total_internal_cost)
        normalized_price = normalize_to_primary_currency(price, project_currency, primary_currency)
        normalized_cost = normalize_to_primary_currency(cost, project_currency, primary_currency)
        sum_price += (
            normalized_price.amount
            if isinstance(normalized_price, Money)
            else Decimal(str(normalized_price))
        )
        sum_cost += (
            normalized_cost.amount
            if isinstance(normalized_cost, Money)
            else Decimal(str(normalized_cost))
        )
    if sum_price <= 0:
        return None
    margin = (sum_price - sum_cost) / sum_price
    return margin.quantize(Decimal("0.0001"))
