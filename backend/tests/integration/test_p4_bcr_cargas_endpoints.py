"""
Paquete P4-bcr-cargas: regresiones de los endpoints financieros.

H05 - /admin/financial-summary devolvía monthlyPayroll SIN cargas sociales y sin amortización,
      mientras blendedBillRate (de la misma respuesta) sí las incluía: el break-even del front
      (monthlyFixedCosts + monthlyPayroll) / blendedBillRate quedaba ~25% por debajo del real.
H48 - /settings/calculations/agency-cost-hour reportaba total_monthly_costs sin la amortización
      de equipos que el blended_cost_rate de la misma respuesta sí incluye.
H12 - exchange_rates_date devolvía datetime.now(): afirmaba que las tasas estáticas de
      2024-01-01 eran de hoy.
H30 - el revenue del dashboard sumaba TODAS las versiones de quote de cada proyecto ganado.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.currency import EXCHANGE_RATES_AS_OF
from app.core.security import create_access_token, get_password_hash
from app.models.cost import CostFixed
from app.models.equipment import EquipmentAmortization
from app.models.organization import Organization
from app.models.project import Project, Quote
from app.models.team import TeamMember
from app.models.user import User

SOCIAL_CONFIG = {"enable_social_charges": True, "total_percentage": 52.852}
MULTIPLIER = Decimal("1.52852")


@pytest.fixture(autouse=True)
def _clear_cache():
    from app.core.cache import get_cache

    get_cache().clear()
    yield
    get_cache().clear()


def _auth_headers(user: User) -> dict:
    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "name": getattr(user, "full_name", None),
            "organization_id": user.organization_id,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def owner_user(db_session: AsyncSession, test_organization: Organization) -> User:
    user = User(
        email=f"owner-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Owner User",
        role="owner",
        role_type="tenant",
        hashed_password=get_password_hash("password123"),
        organization_id=test_organization.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def org_with_equipment(
    db_session: AsyncSession, test_organization: Organization
) -> Organization:
    """
    Org COP: sueldo 4.000.000 (cargas 52,852%), costo fijo 1.000.000,
    equipo de 12.000.000 a 24 meses (500.000/mes), 40 h/semana sin horas no facturables.
    """
    test_organization.settings = {
        "primary_currency": "COP",
        "social_charges_config": dict(SOCIAL_CONFIG),
    }
    db_session.add(test_organization)
    db_session.add(
        CostFixed(
            name="Overhead COP",
            amount_monthly=Decimal("1000000"),
            currency="COP",
            category="Overhead",
            organization_id=test_organization.id,
        )
    )
    db_session.add(
        TeamMember(
            name="Dev COP",
            role="Developer",
            salary_monthly_brute=Decimal("4000000"),
            currency="COP",
            billable_hours_per_week=40,
            non_billable_hours_percentage=Decimal("0"),
            is_active=True,
            organization_id=test_organization.id,
        )
    )
    db_session.add(
        EquipmentAmortization(
            name="MacBook Pro",
            category="Hardware",
            purchase_price=Decimal("12000000"),
            purchase_date=date(2025, 1, 1),
            currency="COP",
            useful_life_months=24,
            salvage_value=Decimal("0"),
            depreciation_method="straight_line",
            is_active=True,
            organization_id=test_organization.id,
        )
    )
    await db_session.commit()
    await db_session.refresh(test_organization)
    return test_organization


@pytest.mark.integration
class TestFinancialSummaryMatchesTheBcr:
    async def test_payroll_and_amortization_are_in_the_cost_base(
        self,
        async_client: AsyncClient,
        owner_user: User,
        org_with_equipment: Organization,
    ):
        response = await async_client.get(
            "/api/v1/admin/financial-summary", headers=_auth_headers(owner_user)
        )
        assert response.status_code == 200, response.text
        payload = response.json()

        fixed_costs = Decimal(str(payload["monthlyFixedCosts"]))
        payroll = Decimal(str(payload["monthlyPayroll"]))
        hours = Decimal(str(payload["totalBillableHours"]))
        blended = Decimal(str(payload["blendedCostRate"]))

        # Antes: monthlyPayroll = 4.000.000 crudo (sin el 52,852%).
        assert abs(payroll - Decimal("4000000") * MULTIPLIER) < Decimal("1")
        # Antes: la amortización no se consultaba en ningún lado del endpoint.
        assert abs(Decimal(str(payload["monthlyAmortization"])) - Decimal("500000")) < Decimal("1")
        assert abs(fixed_costs - Decimal("1500000")) < Decimal("1")

        # Lo que consume el break-even del front: totalCosts / billRate.
        assert abs((fixed_costs + payroll) / hours - blended) < Decimal("1")
        assert abs(Decimal(str(payload["totalMonthlyCosts"])) - (fixed_costs + payroll)) < Decimal(
            "1"
        )


@pytest.mark.integration
class TestAgencyCostHourIncludesAmortization:
    async def test_totals_close_with_the_reported_bcr(
        self,
        async_client: AsyncClient,
        owner_user: User,
        org_with_equipment: Organization,
    ):
        response = await async_client.get(
            "/api/v1/settings/calculations/agency-cost-hour", headers=_auth_headers(owner_user)
        )
        assert response.status_code == 200, response.text
        payload = response.json()

        total_costs = Decimal(str(payload["total_monthly_costs"]))
        total_hours = Decimal(str(payload["total_monthly_hours"]))
        blended = Decimal(str(payload["blended_cost_rate"]))

        # Antes: total_monthly_costs = 7.114.080 (sin los 500.000 de depreciación) contra un
        # blended_cost_rate que sí los incluía.
        assert abs(total_costs - (Decimal("1500000") + Decimal("4000000") * MULTIPLIER)) < Decimal(
            "1"
        )
        assert abs((total_costs / total_hours) - blended) < Decimal("1")
        # El desglose sigue cerrando con el total.
        breakdown = (
            Decimal(str(payload["total_fixed_overhead"]))
            + Decimal(str(payload["total_tools_costs"]))
            + Decimal(str(payload["total_salaries"]))
        )
        assert abs(breakdown - total_costs) < Decimal("1")

    async def test_exchange_rates_date_is_the_rate_vintage(
        self,
        async_client: AsyncClient,
        owner_user: User,
        org_with_equipment: Organization,
    ):
        """H12: el único campo de auditoría de tasas no puede decir datetime.now()."""
        response = await async_client.get(
            "/api/v1/settings/calculations/agency-cost-hour", headers=_auth_headers(owner_user)
        )
        assert response.status_code == 200, response.text
        assert response.json()["exchange_rates_date"] == EXCHANGE_RATES_AS_OF


@pytest.mark.integration
class TestDashboardRevenueCountsOneQuotePerProject:
    async def test_only_the_accepted_version_is_summed(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        owner_user: User,
        test_organization: Organization,
    ):
        project = Project(
            name="Rediseño web",
            client_name="Cliente",
            currency="COP",
            status="Won",
            organization_id=test_organization.id,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        quotes = []
        for version, price in ((1, "10000000"), (2, "12000000"), (3, "15000000")):
            quote = Quote(
                project_id=project.id,
                version=version,
                total_internal_cost=Decimal("1000000"),
                total_client_price=Decimal(price),
            )
            db_session.add(quote)
            quotes.append(quote)
        await db_session.commit()
        for quote in quotes:
            await db_session.refresh(quote)

        project.accepted_quote_id = quotes[-1].id
        db_session.add(project)
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/dashboard/kpis?period=month", headers=_auth_headers(owner_user)
        )
        assert response.status_code == 200, response.text
        payload = response.json()

        # Antes: el JOIN devolvía una fila por versión -> 37.000.000 (+147%).
        assert payload["totalRevenue"] == pytest.approx(15000000.0)
        assert payload["averageTicket"] == pytest.approx(15000000.0)

    async def test_falls_back_to_the_latest_active_version(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        owner_user: User,
        test_organization: Organization,
    ):
        """Sin accepted_quote_id manda la última versión activa, no la suma de todas."""
        project = Project(
            name="Campaña",
            client_name="Cliente 2",
            currency="COP",
            status="Won",
            organization_id=test_organization.id,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        db_session.add(
            Quote(project_id=project.id, version=1, total_client_price=Decimal("10000000"))
        )
        db_session.add(
            Quote(project_id=project.id, version=2, total_client_price=Decimal("12000000"))
        )
        # Versión borrada: no debe contar ni siquiera como candidata.
        db_session.add(
            Quote(
                project_id=project.id,
                version=3,
                total_client_price=Decimal("99000000"),
                is_active=0,
            )
        )
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/dashboard/kpis?period=month", headers=_auth_headers(owner_user)
        )
        assert response.status_code == 200, response.text
        assert response.json()["totalRevenue"] == pytest.approx(12000000.0)
