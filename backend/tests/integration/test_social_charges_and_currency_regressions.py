"""
Regresiones de ronda 3:

1. Recargo patronal: tres implementaciones divergentes del multiplicador de cargas
   sociales (costs.py, calculate_blended_cost_rate y get_organization_cost_breakdown).
   Las dos primeras ignoraban `total_percentage` y el endpoint se contradecía solo.
2. `client_price_override` y `contingency_value` (fijo) no se convertían al cambiar
   la moneda primaria: la siguiente recalculación pisaba la línea con el importe viejo.
3. El contexto financiero de IA dividía Decimal/float y el `except Exception` dejaba
   equipo, horas y BCR en cero para toda org con costos fijos Y equipo.
"""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.ai import _build_financial_context_safe
from app.core.calculations import calculate_blended_cost_rate, get_organization_cost_breakdown
from app.core.security import create_access_token, get_password_hash
from app.models.cost import CostFixed
from app.models.organization import Organization
from app.models.project import Project, Quote, QuoteItem
from app.models.team import TeamMember
from app.models.user import User

# Config real de la org 5: total_percentage (52.852) != suma del desglose (25.192).
ORG5_SOCIAL_CONFIG = {
    "enable_social_charges": True,
    "total_percentage": 52.852,
    "health_percentage": 8.5,
    "pension_percentage": 12.0,
    "arl_percentage": 0.522,
    "parafiscales_percentage": 0,
    "prima_services_percentage": 0,
    "cesantias_percentage": 0,
    "int_cesantias_percentage": 0,
    "vacations_percentage": 4.17,
}


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
async def org5_like(db_session: AsyncSession, test_organization: Organization) -> Organization:
    """Org testigo: COP, sueldos 4.004.500, costos fijos 2.275.050, cargas 52.852%."""
    test_organization.settings = {
        "primary_currency": "COP",
        "social_charges_config": dict(ORG5_SOCIAL_CONFIG),
    }
    db_session.add(test_organization)

    db_session.add(
        CostFixed(
            name="Overhead COP",
            amount_monthly=Decimal("2275050"),
            currency="COP",
            category="Overhead",
            organization_id=test_organization.id,
        )
    )
    db_session.add(
        TeamMember(
            name="Dev COP",
            role="Developer",
            salary_monthly_brute=Decimal("4004500"),
            currency="COP",
            billable_hours_per_week=40,
            non_billable_hours_percentage=Decimal("0"),
            is_active=True,
            organization_id=test_organization.id,
        )
    )
    await db_session.commit()
    await db_session.refresh(test_organization)
    return test_organization


@pytest.mark.integration
class TestSocialChargesMultiplierIsConsistent:
    async def test_all_routes_use_total_percentage(
        self,
        db_session: AsyncSession,
        org5_like: Organization,
    ):
        """Las tres rutas deben aplicar 1.52852, no la suma del desglose (1.25192)."""
        expected_salaries = Decimal("4004500") * Decimal("1.52852")

        # Ruta 1: BCR
        bcr = await calculate_blended_cost_rate(
            db_session,
            primary_currency="COP",
            use_cache=False,
            tenant_id=org5_like.id,
        )
        expected_total = expected_salaries + Decimal("2275050")
        expected_hours = Decimal("40") * Decimal("4.33")
        assert abs(bcr - (expected_total / expected_hours)) < Decimal("1")

        # Ruta 2: anatomía financiera del presupuesto
        breakdown = await get_organization_cost_breakdown(db_session, org5_like.id)
        assert abs(Decimal(str(breakdown["total_salaries"])) - expected_salaries) < Decimal("1")
        expected_talent_ratio = expected_salaries / expected_total
        talent_ratio = Decimal(str(breakdown["talent_ratio"]))
        assert abs(talent_ratio - expected_talent_ratio) < Decimal("0.0005")
        # Con el desglose (1.25192) el ratio daba 0.6879 en vez de 0.7290.
        assert talent_ratio > Decimal("0.72")

    async def test_endpoint_response_is_internally_consistent(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        owner_user: User,
        org5_like: Organization,
        test_settings,
    ):
        """total_monthly_costs / total_monthly_hours debe dar el blended_cost_rate reportado."""
        response = await async_client.get(
            "/api/v1/settings/calculations/agency-cost-hour",
            headers=_auth_headers(owner_user),
        )
        assert response.status_code == 200, response.text
        payload = response.json()

        total_costs = Decimal(str(payload["total_monthly_costs"]))
        total_hours = Decimal(str(payload["total_monthly_hours"]))
        blended = Decimal(str(payload["blended_cost_rate"]))

        assert total_hours > 0
        # Antes: 7.288.363,64 / 857,34 = 8.501,14 vs blended_cost_rate 9.793,09 (15% de gap).
        assert abs((total_costs / total_hours) - blended) < Decimal("1")

        expected_salaries = Decimal("4004500") * Decimal("1.52852")
        assert abs(Decimal(str(payload["total_salaries"])) - expected_salaries) < Decimal("1")


@pytest.mark.integration
class TestPrimaryCurrencyMigrationConvertsOverrides:
    async def test_client_price_override_and_fixed_contingency_are_converted(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_service,
    ):
        """USD -> COP: el override manual y el contingente fijo deben viajar con el resto."""
        from app.services.settings_service import SettingsService

        test_organization.settings = {"primary_currency": "USD"}
        db_session.add(test_organization)

        project = Project(
            name="Override Project",
            client_name="Override Client",
            currency="USD",
            organization_id=test_organization.id,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        quote = Quote(
            project_id=project.id,
            version=1,
            total_internal_cost=Decimal("3000"),
            total_client_price=Decimal("5000"),
            contingency_type="fixed",
            contingency_value=Decimal("1000"),
        )
        db_session.add(quote)
        await db_session.commit()
        await db_session.refresh(quote)

        item = QuoteItem(
            quote_id=quote.id,
            service_id=test_service.id,
            estimated_hours=Decimal("10"),
            internal_cost=Decimal("3000"),
            client_price=Decimal("5000"),
            client_price_override=Decimal("5000"),
        )
        db_session.add(item)
        await db_session.commit()

        item_id = item.id
        quote_id = quote.id

        service = SettingsService(db_session)
        await service.update_primary_currency("COP", organization_id=test_organization.id)

        db_session.expire_all()
        item = (
            await db_session.execute(select(QuoteItem).where(QuoteItem.id == item_id))
        ).scalar_one()
        quote = (await db_session.execute(select(Quote).where(Quote.id == quote_id))).scalar_one()

        client_price = Decimal(str(item.client_price))
        override = Decimal(str(item.client_price_override))

        # El override tiene que seguir a la par del precio convertido, no quedarse en 5.000.
        assert override == client_price
        assert override > Decimal("1000000")
        # Contingente fijo: 1.000 USD no puede quedar como 1.000 COP.
        assert Decimal(str(quote.contingency_value)) > Decimal("1000")


@pytest.mark.integration
class TestAiFinancialContextNumbers:
    async def test_context_has_team_hours_and_bcr_with_costs_and_members(
        self,
        db_session: AsyncSession,
        org5_like: Organization,
    ):
        """Decimal/float rompía la división y el except dejaba todo en cero."""
        context = await _build_financial_context_safe(db_session, org5_like.id, org5_like)

        assert context["primary_currency"] == "COP"
        assert context["total_monthly_costs"] > 0
        assert context["team_size"] > 0, "El TypeError Decimal/float dejaba el equipo en cero"
        assert context["total_monthly_hours"] > 0
        assert context["blended_cost_rate"] > 0

        expected_hours = Decimal("40") * Decimal("4.33")
        assert Decimal(str(context["total_monthly_hours"])) == round(expected_hours, 2)
        # El BCR del contexto es el canónico (fijos + nómina con cargas + amortización),
        # NO costos_fijos/horas: ver tests/integration/test_ai_context_regressions.py.
        expected_bcr = (
            Decimal("2275050") + Decimal("4004500") * Decimal("1.52852")
        ) / expected_hours
        assert abs(Decimal(str(context["blended_cost_rate"])) - expected_bcr) < Decimal("1")
