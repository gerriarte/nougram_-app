"""
Sales projection service for generating revenue forecasts based on services and team capacity
ESTÁNDAR NOUGRAM: Usa Money para precisión en cálculos financieros
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.calculations import calculate_blended_cost_rate
from app.core.capacity import total_monthly_billable_hours
from app.core.logging import get_logger
from app.core.money import Money
from app.models.service import Service
from app.models.team import TeamMember

logger = get_logger(__name__)


async def calculate_sales_projection(
    db: AsyncSession,
    organization_id: int,
    service_ids: list[int],
    estimated_hours_per_service: dict[int, float],
    win_rate: float = 0.85,  # Default 85% win rate
    scenario: str = "realistic",  # "conservative", "realistic", "optimistic"
    period_months: int = 12,
    currency: str = "USD",
) -> dict:
    """
    Calculate sales projection based on services, team capacity, and win rates.

    Args:
        db: Database session
        organization_id: Organization ID
        service_ids: List of service IDs to project
        estimated_hours_per_service: Dictionary mapping service_id to estimated hours
        win_rate: Expected win rate (0.0 to 1.0, default 0.85)
        scenario: Scenario type ("conservative", "realistic", "optimistic")
        period_months: Number of months to project (default 12)
        currency: Currency for calculations

    Returns:
        Dictionary with projection data including monthly breakdowns, totals, and KPIs
    """
    # Adjust win rate based on scenario
    scenario_multipliers = {"conservative": 0.70, "realistic": 0.85, "optimistic": 1.0}
    effective_win_rate = win_rate * scenario_multipliers.get(scenario, 0.85)

    # Get services
    result = await db.execute(
        select(Service).where(
            Service.id.in_(service_ids),
            Service.organization_id == organization_id,
            Service.deleted_at.is_(None),
        )
    )
    services = result.scalars().all()

    if not services:
        raise ValueError("No valid services found for projection")

    # Get BCR (ya retorna Decimal)
    bcr_decimal = await calculate_blended_cost_rate(
        db, currency, use_cache=False, tenant_id=organization_id
    )
    bcr_money = Money(bcr_decimal, currency)  # ESTÁNDAR NOUGRAM: Convertir a Money

    # Get team capacity (total billable hours per month)
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.organization_id == organization_id, TeamMember.is_active
        )
    )
    team_members = result.scalars().all()

    # Implementación única en app/core/capacity.py (sin doble descuento del % no facturable).
    # Se convierte a float porque este servicio expone su respuesta en float por contrato
    # (ver `"bcr": float(bcr_decimal)` más abajo) y la aritmética de utilización de capacidad
    # que sigue es en float. No son importes monetarios, así que no aplica el estándar Decimal.
    total_billable_hours_per_month = float(total_monthly_billable_hours(list(team_members)))

    # ESTÁNDAR NOUGRAM: Calcular proyecciones usando Money
    service_projections = []
    total_projected_revenue_money = Money(0, currency)
    total_projected_cost_money = Money(0, currency)

    for service in services:
        service_id = service.id
        estimated_hours = estimated_hours_per_service.get(service_id, 0)

        if estimated_hours <= 0:
            continue

        # ESTÁNDAR NOUGRAM: Calcular cost usando Money
        cost_money = bcr_money.multiply(Decimal(str(estimated_hours)))

        # ESTÁNDAR NOUGRAM: Calcular price con margen usando Money
        margin_target_decimal = Decimal(str(service.default_margin_target or 0))
        if margin_target_decimal > 0 and margin_target_decimal < 1:
            # apply_margin espera porcentaje (40.0 = 40%)
            price_money = cost_money.apply_margin(float(margin_target_decimal * 100))
        else:
            # Default 40% margin
            price_money = cost_money.apply_margin(40.0)

        # ESTÁNDAR NOUGRAM: Aplicar win rate usando Money
        projected_revenue_money = price_money.multiply(Decimal(str(effective_win_rate)))
        projected_cost_money = cost_money.multiply(
            Decimal(str(effective_win_rate))
        )  # Only cost for won projects

        # Calcular profit y margin
        projected_profit_money = projected_revenue_money.subtract(projected_cost_money)
        margin_percentage = 0.0
        if projected_revenue_money.amount > 0:
            margin_amount = projected_profit_money.amount / projected_revenue_money.amount
            margin_percentage = float(margin_amount * 100)

        service_projections.append(
            {
                "service_id": service_id,
                "service_name": service.name,
                "estimated_hours": estimated_hours,
                "base_price": float(price_money.amount),
                "cost": float(cost_money.amount),
                "projected_revenue": float(projected_revenue_money.amount),
                "projected_cost": float(projected_cost_money.amount),
                "projected_profit": float(projected_profit_money.amount),
                "margin": margin_percentage,
            }
        )

        total_projected_revenue_money = total_projected_revenue_money.add(projected_revenue_money)
        total_projected_cost_money = total_projected_cost_money.add(projected_cost_money)

    # ESTÁNDAR NOUGRAM: Calcular breakdown mensual usando Money
    monthly_projections = []
    revenue_per_month_money = total_projected_revenue_money.divide(Decimal(str(period_months)))
    cost_per_month_money = total_projected_cost_money.divide(Decimal(str(period_months)))

    for month in range(1, period_months + 1):
        profit_per_month_money = revenue_per_month_money.subtract(cost_per_month_money)
        margin_percentage_month = 0.0
        if revenue_per_month_money.amount > 0:
            margin_amount_month = profit_per_month_money.amount / revenue_per_month_money.amount
            margin_percentage_month = float(margin_amount_month * 100)

        monthly_projections.append(
            {
                "month": month,
                "revenue": float(revenue_per_month_money.amount),
                "costs": float(cost_per_month_money.amount),
                "profit": float(profit_per_month_money.amount),
                "margin_percentage": margin_percentage_month,
            }
        )

    # ESTÁNDAR NOUGRAM: Calcular KPIs usando Money
    total_projected_profit_money = total_projected_revenue_money.subtract(
        total_projected_cost_money
    )
    overall_margin = 0.0
    if total_projected_revenue_money.amount > 0:
        margin_amount_total = (
            total_projected_profit_money.amount / total_projected_revenue_money.amount
        )
        overall_margin = float(margin_amount_total * 100)

    # Capacity utilization
    total_estimated_hours = sum(estimated_hours_per_service.values())
    hours_per_month = total_estimated_hours / period_months
    capacity_utilization = (
        (hours_per_month / total_billable_hours_per_month * 100)
        if total_billable_hours_per_month > 0
        else 0
    )

    # ESTÁNDAR NOUGRAM: Convertir Money a float para compatibilidad con endpoint
    return {
        "scenario": scenario,
        "period_months": period_months,
        "win_rate": effective_win_rate,
        "currency": currency,
        "bcr": float(bcr_decimal),  # Convertir Decimal a float para compatibilidad
        "total_billable_hours_per_month": total_billable_hours_per_month,
        "service_projections": service_projections,
        "monthly_projections": monthly_projections,
        "summary": {
            "total_revenue": float(total_projected_revenue_money.amount),
            "total_costs": float(total_projected_cost_money.amount),
            "total_profit": float(total_projected_profit_money.amount),
            "overall_margin_percentage": overall_margin,
            "capacity_utilization_percentage": capacity_utilization,
            "total_estimated_hours": total_estimated_hours,
            "hours_per_month": hours_per_month,
        },
    }
