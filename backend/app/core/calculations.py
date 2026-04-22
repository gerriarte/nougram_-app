"""
Business logic for cost and pricing calculations
ESTÁNDAR NOUGRAM: Usa Money y Decimal para precisión grado bancario
"""

from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.currency import normalize_to_primary_currency
from app.core.logging import get_logger
from app.core.money import Money, sum_money
from app.core.pricing_strategies import PricingStrategyFactory
from app.models.cost import CostFixed
from app.models.equipment import EquipmentAmortization
from app.models.service import Service
from app.models.team import TeamMember

logger = get_logger(__name__)


async def calculate_blended_cost_rate(
    db: AsyncSession,
    primary_currency: str = "USD",
    use_cache: bool = True,
    tenant_id: int | None = None,
    social_charges_config: dict | None = None,
) -> Decimal:
    """
    Calculate the blended cost rate (cost per hour) for the agency.
    ESTÁNDAR NOUGRAM: Retorna Decimal para precisión, se serializa como string en API

    Formula: Total Monthly Costs / Total Billable Hours Available
    """
    from app.core.cache import get_cache

    # Check cache first
    if use_cache:
        cache = get_cache()
        cache_key = f"blended_cost_rate:{primary_currency}:tenant_{tenant_id}"

        # Add social charges config to cache key
        if social_charges_config and social_charges_config.get("enable_social_charges"):
            total_percentage = social_charges_config.get("total_percentage", 0)
            cache_key += f":social_{total_percentage}"

        cached_value = cache.get(cache_key)
        if cached_value is not None:
            # Convert cached float to Decimal for consistency
            return Decimal(str(cached_value))

    # Get all fixed costs (excluding soft-deleted) and convert to Money
    query = select(CostFixed).where(CostFixed.deleted_at.is_(None))
    if tenant_id is not None:
        query = query.where(CostFixed.organization_id == tenant_id)

    result = await db.execute(query)
    fixed_costs = result.scalars().all()

    fixed_costs_money = []
    for cost in fixed_costs:
        # Ensure currency has a value (default to USD if None)
        cost_currency = cost.currency or "USD"
        # ESTÁNDAR NOUGRAM: normalize_to_primary_currency puede retornar Money o float
        normalized = normalize_to_primary_currency(
            Decimal(str(cost.amount_monthly)),  # Convertir Numeric a Decimal
            cost_currency,
            primary_currency,
        )
        # Si retorna Money, usarlo directamente; si retorna float, convertir a Money
        if isinstance(normalized, Money):
            fixed_costs_money.append(normalized)
        else:
            fixed_costs_money.append(Money(normalized, primary_currency))

    # Get all active team members and normalize their salaries
    # Filter by tenant if tenant_id is provided
    query = select(TeamMember).where(TeamMember.is_active)
    if tenant_id is not None:
        query = query.where(TeamMember.organization_id == tenant_id)
    result = await db.execute(query)
    team_members = result.scalars().all()

    # Get organization settings for social charges (Sprint 18)
    social_charges_multiplier = Decimal("1.0")
    if tenant_id is not None:
        try:
            from app.models.organization import Organization

            org_result = await db.execute(select(Organization).where(Organization.id == tenant_id))
            org = org_result.scalar_one_or_none()
            if org and org.settings and org.settings.get("social_charges_config"):
                social_config = org.settings.get("social_charges_config", {})
                if social_config.get("enable_social_charges", False):
                    # Calculate multiplier: 1 + (sum of all percentages / 100)
                    total_percentage = Decimal("0")

                    # Sum all individual components if they exist (Colombia Legal Breakdown)
                    total_percentage += Decimal(str(social_config.get("health_percentage", 0) or 0))
                    total_percentage += Decimal(
                        str(social_config.get("pension_percentage", 0) or 0)
                    )
                    total_percentage += Decimal(str(social_config.get("arl_percentage", 0) or 0))
                    total_percentage += Decimal(
                        str(social_config.get("parafiscales_percentage", 0) or 0)
                    )
                    total_percentage += Decimal(
                        str(social_config.get("prima_services_percentage", 0) or 0)
                    )
                    total_percentage += Decimal(
                        str(social_config.get("cesantias_percentage", 0) or 0)
                    )
                    total_percentage += Decimal(
                        str(social_config.get("int_cesantias_percentage", 0) or 0)
                    )
                    total_percentage += Decimal(
                        str(social_config.get("vacations_percentage", 0) or 0)
                    )

                    # Fallback to total_percentage if no individual components are set
                    if total_percentage == 0:
                        total_percentage = Decimal(
                            str(social_config.get("total_percentage", 0) or 0)
                        )

                    if total_percentage > 0:
                        social_charges_multiplier = Decimal("1") + (
                            total_percentage / Decimal("100")
                        )
        except Exception as e:
            logger.warning(f"Error getting social charges config: {e}")
            # If there's an error getting org settings, use default multiplier
            pass

    # Calculate total salaries with social charges using Money
    salary_amounts = []
    for member in team_members:
        # Ensure currency has a value (default to USD if None)
        member_currency = member.currency or "USD"
        normalized = normalize_to_primary_currency(
            member.salary_monthly_brute, member_currency, primary_currency
        )
        salary_money = Money(normalized, primary_currency)
        # Per-member: skip org multiplier when member opted out of social charges
        effective_mult = (
            social_charges_multiplier
            if getattr(member, "apply_social_charges", True)
            else Decimal("1")
        )
        salary_with_charges = salary_money.multiply(effective_mult)
        salary_amounts.append(salary_with_charges)

        # #region agent log
        import json
        import os

        try:
            log_data = {
                "location": "calculations.py:131",
                "message": "Team member salary in calculate_blended_cost_rate",
                "data": {
                    "member_id": member.id,
                    "member_name": member.name,
                    "salary_monthly_brute": str(member.salary_monthly_brute),
                    "member_currency": member_currency,
                    "normalized": str(normalized)
                    if not isinstance(normalized, Money)
                    else str(normalized.amount),
                    "salary_with_charges": str(salary_with_charges.amount),
                    "social_charges_multiplier": str(social_charges_multiplier),
                },
                "timestamp": __import__("time").time() * 1000,
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "D",
            }
            log_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".cursor", "debug.log"
            )
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data) + "\n")
        except:
            pass
        # #endregion

    # Get amortization assets and include monthly depreciation in fixed costs.
    equipment_query = select(EquipmentAmortization).where(
        EquipmentAmortization.deleted_at.is_(None), EquipmentAmortization.is_active
    )
    if tenant_id is not None:
        equipment_query = equipment_query.where(EquipmentAmortization.organization_id == tenant_id)
    equipment_result = await db.execute(equipment_query)
    equipment_assets = equipment_result.scalars().all()

    equipment_amortization_money = []
    for asset in equipment_assets:
        useful_life = int(asset.useful_life_months or 0)
        if useful_life <= 0:
            continue
        purchase_price = Decimal(str(asset.purchase_price or 0))
        salvage_value = Decimal(str(asset.salvage_value or 0))
        monthly_depreciation = (purchase_price - salvage_value) / Decimal(str(useful_life))
        if monthly_depreciation <= 0:
            continue
        normalized = normalize_to_primary_currency(
            monthly_depreciation, asset.currency or "USD", primary_currency
        )
        if isinstance(normalized, Money):
            equipment_amortization_money.append(normalized)
        else:
            equipment_amortization_money.append(Money(normalized, primary_currency))

    # Sum all costs using Money
    all_costs = fixed_costs_money + equipment_amortization_money + salary_amounts
    total_monthly_costs_money = sum_money(all_costs)

    # #region agent log
    try:
        log_data = {
            "location": "calculations.py:135",
            "message": "Total costs calculated",
            "data": {
                "fixed_costs_count": len(fixed_costs_money),
                "salary_amounts_count": len(salary_amounts),
                "total_monthly_costs_money": str(total_monthly_costs_money.amount)
                if total_monthly_costs_money
                else "None",
                "total_monthly_costs_money_currency": total_monthly_costs_money.currency
                if total_monthly_costs_money
                else "None",
            },
            "timestamp": __import__("time").time() * 1000,
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "D",
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data) + "\n")
    except:
        pass
    # #endregion

    if total_monthly_costs_money is None:
        return Decimal("0")

    # Calculate total billable hours per month (assuming 4.33 weeks per month)
    # Adjust for non-billable hours percentage (Sprint 14)
    hours_per_month = Decimal("0")
    for member in team_members:
        non_billable = getattr(member, "non_billable_hours_percentage", 0.0) or 0.0
        billable_factor = Decimal("1") - Decimal(str(non_billable))
        hours = Decimal(str(member.billable_hours_per_week)) * Decimal("4.33") * billable_factor
        hours_per_month += hours

    # Calculate cost per hour using Money
    if hours_per_month > 0:
        cost_per_hour_money = total_monthly_costs_money.divide(float(hours_per_month))
        cost_per_hour = cost_per_hour_money.amount  # Return Decimal

        # #region agent log
        try:
            log_data = {
                "location": "calculations.py:152",
                "message": "BCR calculated",
                "data": {
                    "hours_per_month": str(hours_per_month),
                    "cost_per_hour": str(cost_per_hour),
                    "cost_per_hour_money_amount": str(cost_per_hour_money.amount),
                    "cost_per_hour_money_currency": cost_per_hour_money.currency,
                },
                "timestamp": __import__("time").time() * 1000,
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "D",
            }
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data) + "\n")
        except:
            pass
        # #endregion
    else:
        cost_per_hour = Decimal("0")

        # #region agent log
        try:
            log_data = {
                "location": "calculations.py:154",
                "message": "BCR is zero (no hours)",
                "data": {"hours_per_month": str(hours_per_month), "cost_per_hour": "0"},
                "timestamp": __import__("time").time() * 1000,
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "D",
            }
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data) + "\n")
        except:
            pass
        # #endregion

    # Cache the result (5 minutes TTL) - cache as float for compatibility
    if use_cache:
        cache = get_cache()
        # Reconstruct cache key same way as above (including social charges)
        cache_key = f"blended_cost_rate:{primary_currency}:tenant_{tenant_id}"
        if tenant_id is not None:
            try:
                from app.models.organization import Organization

                org_result = await db.execute(
                    select(Organization).where(Organization.id == tenant_id)
                )
                org = org_result.scalar_one_or_none()
                if org and org.settings and org.settings.get("social_charges_config"):
                    social_config = org.settings.get("social_charges_config", {})
                    if social_config.get("enable_social_charges", False):
                        total_percentage = social_config.get("total_percentage", 0)
                        cache_key += f":social_{total_percentage}"
            except Exception:
                pass
        # Cache as float for backward compatibility
        cache.set(cache_key, float(cost_per_hour), ttl_seconds=300)

    return cost_per_hour


async def calculate_quote_totals(
    db: AsyncSession,
    items: list[dict],
    blended_cost_rate: float,
    tax_ids: list[int] = None,
    organization_id: int | None = None,
) -> dict:
    """
    Calculate total internal cost, client price, taxes, and margin for a quote.

    **DEPRECATED**: This function is deprecated. Use `calculate_quote_totals_enhanced()` instead.
    This function is kept for backward compatibility but should not be used in new code.

    Args:
        db: Database session
        items: List of items with service_id and estimated_hours
        blended_cost_rate: Current blended cost rate
        tax_ids: List of tax IDs to apply (optional)

    Returns:
        Dict with total_internal_cost, total_client_price, total_taxes, total_with_taxes, margin_percentage, taxes
    """
    from app.models.tax import Tax

    total_internal_cost = 0.0
    total_client_price = 0.0

    for item in items:
        service_id = item.get("service_id")
        estimated_hours = item.get("estimated_hours", 0)

        # Get service details (excluding soft-deleted services)
        result = await db.execute(
            select(Service).where(Service.id == service_id, Service.deleted_at.is_(None))
        )
        service = result.scalar_one_or_none()

        if service:
            # Calculate internal cost
            internal_cost = blended_cost_rate * estimated_hours
            total_internal_cost += internal_cost

            # Calculate client price (with margin)
            client_price = internal_cost / (1 - service.default_margin_target)
            total_client_price += client_price

    # Calculate taxes if provided
    total_taxes = 0.0
    taxes_breakdown = []

    if tax_ids:
        tax_conditions = [
            Tax.id.in_(tax_ids),
            Tax.is_active,
            Tax.deleted_at.is_(None),
        ]
        if organization_id is not None:
            tax_conditions.append(Tax.organization_id == organization_id)
        result = await db.execute(select(Tax).where(and_(*tax_conditions)))
        taxes = result.scalars().all()

        for tax in taxes:
            tax_amount = total_client_price * (tax.percentage / 100)
            total_taxes += tax_amount
            taxes_breakdown.append(
                {
                    "id": tax.id,
                    "name": tax.name,
                    "code": tax.code,
                    "percentage": tax.percentage,
                    "amount": tax_amount,
                }
            )

    total_with_taxes = total_client_price + total_taxes

    # Calculate margin percentage (based on price before taxes)
    if total_client_price > 0:
        margin_percentage = (total_client_price - total_internal_cost) / total_client_price
    else:
        margin_percentage = 0.0

    return {
        "total_internal_cost": total_internal_cost,
        "total_client_price": total_client_price,
        "total_taxes": total_taxes,
        "total_with_taxes": total_with_taxes,
        "margin_percentage": margin_percentage,
        "taxes": taxes_breakdown,
    }


async def calculate_quote_totals_enhanced(
    db: AsyncSession,
    items: list[dict],
    blended_cost_rate: float,
    tax_ids: list[int] = None,
    expenses: list[dict] = None,
    target_margin_percentage: Decimal | None = None,
    revisions_included: int = 2,
    revision_cost_per_additional: float | None = None,
    revisions_count: int | None = None,
    currency: str = "USD",  # ESTÁNDAR NOUGRAM: Especificar moneda para precisión
    organization_id: int | None = None,
) -> dict:
    """
    Enhanced quote calculation supporting multiple pricing types, expenses, and revisions (Sprint 15-16)
    ESTÁNDAR NOUGRAM: Usa Money para precisión grado bancario

    - hourly: Hours × BCR (existing logic)
    - fixed: fixed_price × quantity
    - recurring: recurring_price (based on billing frequency)
    - project_value: Custom project value
    - expenses: Third-party costs with markup
    - revisions: Additional cost for revisions beyond included count

    Args:
        db: Database session
        items: List of items with service_id and pricing information
        blended_cost_rate: Current blended cost rate (for hourly calculations) - puede ser Decimal o float
        tax_ids: List of tax IDs to apply (optional)
        expenses: List of expenses with cost, markup_percentage, quantity (optional)
        target_margin_percentage: Target margin for entire quote (0-1, e.g., 0.40 = 40%)
        revisions_included: Number of included revisions (default: 2)
        revision_cost_per_additional: Cost per additional revision (optional)
        revisions_count: Actual number of revisions requested (optional, for calculation)
        currency: Currency code (USD, COP, EUR, ARS) - ESTÁNDAR NOUGRAM

    Returns:
        Dict with total_internal_cost, total_client_price, total_expenses_cost,
        total_expenses_client_price, total_taxes, total_with_taxes, margin_percentage,
        taxes, items, expenses, revisions_cost
    """
    from app.models.tax import Tax

    # Defensive normalization for legacy payloads that may still send 35 instead of 0.35.
    if target_margin_percentage is not None:
        if not isinstance(target_margin_percentage, Decimal):
            target_margin_percentage = Decimal(str(target_margin_percentage))
        if target_margin_percentage > Decimal("1") and target_margin_percentage <= Decimal("100"):
            target_margin_percentage = target_margin_percentage / Decimal("100")
        elif target_margin_percentage > Decimal("100") or target_margin_percentage < Decimal("0"):
            target_margin_percentage = None

    # ESTÁNDAR NOUGRAM: Usar Money para todos los cálculos
    total_internal_cost_money = Money(0, currency)
    total_client_price_money = Money(0, currency)
    items_breakdown = []

    # Normalizar blended_cost_rate a Decimal para mantener precisión
    bcr_decimal = (
        blended_cost_rate
        if isinstance(blended_cost_rate, Decimal)
        else Decimal(str(blended_cost_rate))
    )

    # First pass: Calculate internal costs and client prices for all items
    for item in items:
        service_id = item.get("service_id")
        pricing_type = item.get("pricing_type")  # Can override service pricing_type

        # Get service details (excluding soft-deleted services)
        result = await db.execute(
            select(Service).where(Service.id == service_id, Service.deleted_at.is_(None))
        )
        service = result.scalar_one_or_none()

        if not service:
            continue

        # Use item pricing_type if provided, otherwise use service pricing_type
        effective_pricing_type = pricing_type or service.pricing_type or "hourly"

        # Get pricing strategy and calculate costs
        strategy = PricingStrategyFactory.get_strategy(effective_pricing_type)
        pricing_result = strategy.calculate(item, service, bcr_decimal)

        internal_cost = pricing_result["internal_cost"]
        client_price = pricing_result.get("client_price", 0.0)  # Get client_price from strategy

        # Skip items with zero cost
        if internal_cost == 0.0:
            continue

        # Convert to Money
        internal_cost_money = Money(internal_cost, currency)
        client_price_money = Money(client_price, currency)

        total_internal_cost_money = total_internal_cost_money.add(internal_cost_money)

        # Apply target margin only to margin-driven pricing types.
        # Fixed/project-value items keep their explicit client prices.
        if (
            target_margin_percentage is not None
            and Decimal("0") < target_margin_percentage < Decimal("1")
            and effective_pricing_type in ("hourly", "recurring")
        ):
            margin_percent_decimal = target_margin_percentage
            # #region agent log
            try:
                import json
                import os

                log_data = {
                    "location": "calculations.py:365",
                    "message": "before apply_margin (per item)",
                    "data": {
                        "target_margin_percentage": str(target_margin_percentage),
                        "target_margin_percentage_type": str(
                            type(target_margin_percentage).__name__
                        ),
                        "margin_percent_decimal": str(margin_percent_decimal),
                        "margin_percent_decimal_type": str(type(margin_percent_decimal).__name__),
                        "margin_percent_decimal_x_100": str(
                            margin_percent_decimal * Decimal("100")
                        ),
                        "margin_percent_decimal_x_100_type": str(
                            type(margin_percent_decimal * Decimal("100")).__name__
                        ),
                    },
                    "timestamp": __import__("time").time() * 1000,
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "B",
                }
                log_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), ".cursor", "debug.log"
                )
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_data) + "\n")
            except:
                pass
            # #endregion
            client_price_money = internal_cost_money.apply_margin(
                margin_percent_decimal * Decimal("100")
            )  # Convert to percentage

        total_client_price_money = total_client_price_money.add(client_price_money)

        # Calculate margin for this item
        item_margin = 0.0
        if client_price_money.amount > 0:
            margin_amount = client_price_money.subtract(internal_cost_money)
            item_margin = float(margin_amount.amount / client_price_money.amount)

        # Store item data for breakdown
        items_breakdown.append(
            {
                "service_id": service_id,
                "service_name": service.name,
                "pricing_type": effective_pricing_type,
                "internal_cost": float(internal_cost_money.amount),
                "client_price": float(client_price_money.amount),
                "margin_percentage": item_margin,
            }
        )

    # Calculate expenses (Sprint 15: third-party costs with markup)
    # ESTÁNDAR NOUGRAM: Usar Money para expenses
    total_expenses_cost_money = Money(0, currency)
    total_expenses_client_price_money = Money(0, currency)
    expenses_breakdown = []

    if expenses:
        for expense in expenses:
            cost = expense.get("cost", 0)
            markup_percentage = expense.get("markup_percentage", 0.0)
            quantity = expense.get("quantity", 1.0)

            if cost <= 0:
                continue

            # ESTÁNDAR NOUGRAM: Calcular expenses usando Money
            expense_cost_money = Money(cost, currency).multiply(quantity)
            markup_decimal = Decimal(str(markup_percentage))
            expense_client_price_money = expense_cost_money.multiply(Decimal("1") + markup_decimal)

            total_expenses_cost_money = total_expenses_cost_money.add(expense_cost_money)
            total_expenses_client_price_money = total_expenses_client_price_money.add(
                expense_client_price_money
            )

            # Store expense breakdown
            expenses_breakdown.append(
                {
                    "name": expense.get("name", "Unknown Expense"),
                    "description": expense.get("description"),
                    "category": expense.get("category"),
                    "cost": float(expense_cost_money.amount),
                    "quantity": quantity,
                    "markup_percentage": float(markup_percentage * 100),  # Convert to percentage
                    "expense_cost": float(expense_cost_money.amount),
                    "client_price": float(expense_client_price_money.amount),
                }
            )

    # Add expenses to totals
    total_internal_cost_money = total_internal_cost_money.add(total_expenses_cost_money)

    # Total client price is always built from item-level prices + expense client prices.
    total_client_price_money = total_client_price_money.add(total_expenses_client_price_money)

    # Calculate additional revision costs (Sprint 16)
    # ESTÁNDAR NOUGRAM: Usar Money para revisions
    revisions_cost_money = Money(0, currency)
    if (
        revision_cost_per_additional is not None
        and revision_cost_per_additional >= 0
        and revisions_count is not None
    ):
        if revisions_count > revisions_included:
            additional_revisions = revisions_count - revisions_included
            revision_cost_money = Money(revision_cost_per_additional, currency)
            revisions_cost_money = revision_cost_money.multiply(additional_revisions)
            total_client_price_money = total_client_price_money.add(revisions_cost_money)

    # Calculate taxes if provided
    # ESTÁNDAR NOUGRAM: Usar Money para taxes
    total_taxes_money = Money(0, currency)
    taxes_breakdown = []

    if tax_ids:
        tax_conditions = [
            Tax.id.in_(tax_ids),
            Tax.is_active,
            Tax.deleted_at.is_(None),
        ]
        if organization_id is not None:
            tax_conditions.append(Tax.organization_id == organization_id)
        result = await db.execute(select(Tax).where(and_(*tax_conditions)))
        taxes = result.scalars().all()

        for tax in taxes:
            # ESTÁNDAR NOUGRAM: Aplicar porcentaje usando Money
            # Convertir tax.percentage a float si es Decimal para evitar problemas de tipo
            tax_percentage = (
                float(tax.percentage) if isinstance(tax.percentage, Decimal) else tax.percentage
            )
            tax_amount_money = total_client_price_money.apply_percentage(tax_percentage)
            total_taxes_money = total_taxes_money.add(tax_amount_money)

            taxes_breakdown.append(
                {
                    "id": tax.id,
                    "name": tax.name,
                    "code": tax.code,
                    "percentage": tax.percentage,
                    "amount": float(tax_amount_money.amount),
                }
            )

    total_with_taxes_money = total_client_price_money.add(total_taxes_money)

    # Calculate margin percentage (based on price before taxes)
    # ESTÁNDAR NOUGRAM: Calcular margen usando Money
    if total_client_price_money.amount > 0:
        margin_amount_money = total_client_price_money.subtract(total_internal_cost_money)
        margin_percentage = float(margin_amount_money.amount / total_client_price_money.amount)
    else:
        margin_percentage = 0.0

    # ESTÁNDAR NOUGRAM: Retornar valores como float (compatibilidad) pero calculados con Money
    return {
        "total_internal_cost": float(total_internal_cost_money.amount),
        "total_client_price": float(total_client_price_money.amount),
        "total_expenses_cost": float(total_expenses_cost_money.amount),
        "total_expenses_client_price": float(total_expenses_client_price_money.amount),
        "total_taxes": float(total_taxes_money.amount),
        "total_with_taxes": float(total_with_taxes_money.amount),
        "margin_percentage": margin_percentage,
        "target_margin_percentage": target_margin_percentage,  # Include target margin in response
        "taxes": taxes_breakdown,
        "items": items_breakdown,  # Detailed breakdown per item
        "expenses": expenses_breakdown,  # Detailed breakdown per expense (Sprint 15)
        "revisions_cost": float(
            revisions_cost_money.amount
        ),  # Additional cost for revisions (Sprint 16)
        "revisions_included": revisions_included,
        "revisions_count": revisions_count,
    }


async def get_organization_cost_breakdown(db: AsyncSession, organization_id: int) -> dict:
    """
    Get the breakdown of monthly costs for an organization (Salaries vs Fixed).
    Used to determine cost ratios for rentability analysis.
    """
    from app.models.organization import Organization

    # 1. Get primary currency and organization
    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    org = result.scalar_one_or_none()
    if not org:
        return {"talent_ratio": 0.8, "overhead_ratio": 0.2, "total_monthly_costs": 0.0}

    primary_currency = (org.settings or {}).get("primary_currency", "USD")

    # 2. Get fixed costs
    query = select(CostFixed).where(
        CostFixed.deleted_at.is_(None), CostFixed.organization_id == organization_id
    )
    result = await db.execute(query)
    fixed_costs = result.scalars().all()

    total_fixed = 0.0
    for cost in fixed_costs:
        # ESTÁNDAR NOUGRAM: normalize_to_primary_currency puede retornar Money o float
        normalized = normalize_to_primary_currency(
            Decimal(str(cost.amount_monthly)), cost.currency or "USD", primary_currency
        )
        # Convertir a float para compatibilidad con código legacy
        total_fixed += float(normalized) if isinstance(normalized, Money) else normalized

    # Include amortization assets into fixed monthly costs.
    equipment_query = select(EquipmentAmortization).where(
        EquipmentAmortization.deleted_at.is_(None),
        EquipmentAmortization.is_active,
        EquipmentAmortization.organization_id == organization_id,
    )
    equipment_result = await db.execute(equipment_query)
    equipment_assets = equipment_result.scalars().all()
    for asset in equipment_assets:
        useful_life = int(asset.useful_life_months or 0)
        if useful_life <= 0:
            continue
        purchase_price = Decimal(str(asset.purchase_price or 0))
        salvage_value = Decimal(str(asset.salvage_value or 0))
        monthly_depreciation = (purchase_price - salvage_value) / Decimal(str(useful_life))
        if monthly_depreciation <= 0:
            continue
        normalized = normalize_to_primary_currency(
            monthly_depreciation, asset.currency or "USD", primary_currency
        )
        total_fixed += float(normalized) if isinstance(normalized, Money) else normalized

    # 3. Get salaries with social charges
    query = select(TeamMember).where(
        TeamMember.is_active, TeamMember.organization_id == organization_id
    )
    result = await db.execute(query)
    team_members = result.scalars().all()

    social_charges_multiplier = 1.0
    if org.settings and org.settings.get("social_charges_config"):
        social_config = org.settings.get("social_charges_config", {})
        if social_config.get("enable_social_charges", False):
            total_percentage = sum(
                [
                    social_config.get("health_percentage", 0) or 0,
                    social_config.get("pension_percentage", 0) or 0,
                    social_config.get("arl_percentage", 0) or 0,
                    social_config.get("parafiscales_percentage", 0) or 0,
                    social_config.get("prima_services_percentage", 0) or 0,
                    social_config.get("cesantias_percentage", 0) or 0,
                    social_config.get("int_cesantias_percentage", 0) or 0,
                    social_config.get("vacations_percentage", 0) or 0,
                ]
            )
            if total_percentage == 0:
                total_percentage = social_config.get("total_percentage", 0) or 0
            social_charges_multiplier = 1.0 + (total_percentage / 100.0)

    total_salaries = 0.0
    for member in team_members:
        # ESTÁNDAR NOUGRAM: normalize_to_primary_currency puede retornar Money o float
        normalized = normalize_to_primary_currency(
            Decimal(str(member.salary_monthly_brute)), member.currency or "USD", primary_currency
        )
        # Convertir a float para compatibilidad con código legacy
        normalized_float = float(normalized) if isinstance(normalized, Money) else normalized
        member_mult = (
            social_charges_multiplier if getattr(member, "apply_social_charges", True) else 1.0
        )
        total_salaries += normalized_float * member_mult

    total_costs = total_fixed + total_salaries

    if total_costs > 0:
        return {
            "talent_ratio": total_salaries / total_costs,
            "overhead_ratio": total_fixed / total_costs,
            "total_monthly_costs": total_costs,
            "total_salaries": total_salaries,
            "total_fixed": total_fixed,
            "primary_currency": primary_currency,
        }

    return {
        "talent_ratio": 0.8,
        "overhead_ratio": 0.2,
        "total_monthly_costs": 0.0,
        "primary_currency": primary_currency,
    }


async def calculate_rentability_analysis(
    db: AsyncSession, quote_id: int, organization_id: int
) -> dict:
    """
    Break down the financial anatomy of a proposal.
    ESTÁNDAR NOUGRAM: Usa Money para precisión grado bancario en todos los cálculos
    """
    from sqlalchemy.orm import selectinload

    from app.models.project import Project, Quote

    # 1. Fetch Quote with all details
    result = await db.execute(
        select(Quote)
        .options(
            selectinload(Quote.items),
            selectinload(Quote.expenses),
            selectinload(Quote.project).selectinload(Project.taxes),
        )
        .where(Quote.id == quote_id)
    )
    quote = result.scalar_one_or_none()
    if not quote:
        return None

    # ESTÁNDAR NOUGRAM: Obtener currency del project
    currency = quote.project.currency if quote.project else "USD"

    # 2. Get organization cost ratios
    breakdown = await get_organization_cost_breakdown(db, organization_id)
    talent_ratio = breakdown["talent_ratio"]
    overhead_ratio = breakdown["overhead_ratio"]

    # ESTÁNDAR NOUGRAM: Inicializar categorías usando Money
    operating_talent_money = Money(0, currency)
    operating_overhead_money = Money(0, currency)
    saas_tools_money = Money(0, currency)
    variable_costs_money = Money(0, currency)

    # 3. Process Items (Talent vs Overhead split)
    for item in quote.items:
        # ESTÁNDAR NOUGRAM: Convertir internal_cost a Money
        internal_cost_decimal = (
            Decimal(str(item.internal_cost)) if item.internal_cost else Decimal("0")
        )
        internal_cost_money = Money(internal_cost_decimal, currency)

        # ESTÁNDAR NOUGRAM: Aplicar ratios usando Money
        operating_talent_money = operating_talent_money.add(
            internal_cost_money.multiply(talent_ratio)
        )
        operating_overhead_money = operating_overhead_money.add(
            internal_cost_money.multiply(overhead_ratio)
        )

    # 4. Process Expenses
    for expense in quote.expenses:
        # ESTÁNDAR NOUGRAM: Convertir cost y quantity a Money
        cost_decimal = Decimal(str(expense.cost)) if expense.cost else Decimal("0")
        quantity_decimal = Decimal(str(expense.quantity)) if expense.quantity else Decimal("1")
        cost_money = Money(cost_decimal, currency)
        total_expense_cost_money = cost_money.multiply(float(quantity_decimal))

        category = (expense.category or "").lower()

        # Categorize: 'SaaS', 'Tools', 'Licenses' -> operating_overhead/saas_tools
        if any(
            term in category
            for term in ["saas", "tool", "license", "software", "suscrip", "licencia"]
        ):
            saas_tools_money = saas_tools_money.add(total_expense_cost_money)
        else:
            variable_costs_money = variable_costs_money.add(total_expense_cost_money)

    # 5. Calculate Taxes Burden
    # ESTÁNDAR NOUGRAM: Convertir total_client_price a Money
    total_client_price_decimal = (
        Decimal(str(quote.total_client_price)) if quote.total_client_price else Decimal("0")
    )
    total_client_price_money = Money(total_client_price_decimal, currency)

    total_taxes_money = Money(0, currency)
    taxes_list = []

    if quote.project and quote.project.taxes:
        for tax in quote.project.taxes:
            # ESTÁNDAR NOUGRAM: Aplicar porcentaje usando Money
            tax_amount_money = total_client_price_money.apply_percentage(tax.percentage)
            total_taxes_money = total_taxes_money.add(tax_amount_money)

            # Calcular porcentaje para display
            tax_percentage = 0.0
            if total_client_price_money.amount > 0:
                tax_percentage = float(
                    (tax_amount_money.amount / total_client_price_money.amount) * 100
                )

            taxes_list.append(
                {
                    "concept": tax.name,
                    "amount": float(tax_amount_money.amount),
                    "percentage": tax_percentage,
                }
            )

    # ESTÁNDAR NOUGRAM: Agregar categorías usando Money
    resumen_categories = []

    # Operating Costs
    if operating_talent_money.amount > 0:
        talent_percentage = 0.0
        if total_client_price_money.amount > 0:
            talent_percentage = float(
                (operating_talent_money.amount / total_client_price_money.amount) * 100
            )

        resumen_categories.append(
            {
                "category": "Costos de Operación",
                "concept": "Talento y Recursos",
                "amount": float(operating_talent_money.amount),
                "percentage": talent_percentage,
                "description": "Costo proporcional de salarios y cargas prestacionales",
            }
        )

    if operating_overhead_money.amount > 0:
        overhead_percentage = 0.0
        if total_client_price_money.amount > 0:
            overhead_percentage = float(
                (operating_overhead_money.amount / total_client_price_money.amount) * 100
            )

        resumen_categories.append(
            {
                "category": "Costos de Operación",
                "concept": "Overhead Fijo",
                "amount": float(operating_overhead_money.amount),
                "percentage": overhead_percentage,
                "description": "Costo proporcional de oficina, servicios y administración",
            }
        )

    if saas_tools_money.amount > 0:
        saas_percentage = 0.0
        if total_client_price_money.amount > 0:
            saas_percentage = float(
                (saas_tools_money.amount / total_client_price_money.amount) * 100
            )

        resumen_categories.append(
            {
                "category": "Costos de Operación",
                "concept": "Software y Herramientas",
                "amount": float(saas_tools_money.amount),
                "percentage": saas_percentage,
                "description": "Gastos directos en licencias y herramientas para el proyecto",
            }
        )

    # Variable Costs
    if variable_costs_money.amount > 0:
        variable_percentage = 0.0
        if total_client_price_money.amount > 0:
            variable_percentage = float(
                (variable_costs_money.amount / total_client_price_money.amount) * 100
            )

        resumen_categories.append(
            {
                "category": "Costos Variables",
                "concept": "Gastos de Terceros / Materiales",
                "amount": float(variable_costs_money.amount),
                "percentage": variable_percentage,
                "description": "Costos externos vinculados directamente a la entrega",
            }
        )

    # Taxes
    for tax_item in taxes_list:
        resumen_categories.append(
            {
                "category": "Carga Tributaria",
                "concept": tax_item["concept"],
                "amount": tax_item["amount"],
                "percentage": tax_item["percentage"],
                "description": "Impuesto aplicado sobre el valor bruto",
            }
        )

    # ESTÁNDAR NOUGRAM: Calcular Net Profit usando Money
    total_internal_cost_decimal = (
        Decimal(str(quote.total_internal_cost)) if quote.total_internal_cost else Decimal("0")
    )
    total_internal_cost_money = Money(total_internal_cost_decimal, currency)

    net_profit_money = total_client_price_money.subtract(total_internal_cost_money).subtract(
        total_taxes_money
    )

    net_profit_margin = 0.0
    if total_client_price_money.amount > 0:
        margin_amount = net_profit_money.amount / total_client_price_money.amount
        net_profit_margin = float(margin_amount * 100)

    status = "healthy"
    if net_profit_margin < 15:
        status = "critical"
    elif net_profit_margin < 30:
        status = "warning"

    # ESTÁNDAR NOUGRAM: Convertir Money a float para compatibilidad con endpoints
    return {
        "quote_id": quote_id,
        "total_client_price": float(total_client_price_money.amount),
        "total_internal_cost": float(total_internal_cost_money.amount),
        "total_taxes": float(total_taxes_money.amount),
        "net_profit_amount": float(net_profit_money.amount),
        "net_profit_margin": net_profit_margin,
        "categories": resumen_categories,
        "status": status,
    }
