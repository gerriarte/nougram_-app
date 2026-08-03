"""
Regresiones de ronda 2:

1. Persistencia del breakdown por ítem: dos ítems del mismo servicio se guardaban
   con el precio y el costo del último (breakdown indexado por service_id).
2. /settings/calculations/agency-cost-hour reventaba con TypeError (float × Decimal)
   cuando algún miembro tenía non_billable_hours_percentage > 0, y el except genérico
   devolvía todo en cero con primary_currency='USD'.
3. El contexto financiero de IA solo seteaba primary_currency cuando fallaba la carga
   de proyectos, así que en el camino feliz la IA cotizaba en USD.
"""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.ai import _build_financial_context_safe
from app.core.security import create_access_token, get_password_hash
from app.models.organization import Organization
from app.models.project import Quote, QuoteItem
from app.models.team import TeamMember
from app.models.user import User
from app.services.credit_service import CreditService


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


@pytest.mark.integration
class TestDuplicateServiceItemsPersistence:
    async def test_two_items_same_service_keep_their_own_numbers(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        owner_user: User,
        test_organization: Organization,
        test_service,
        test_settings,
        test_team_member,
    ):
        """Las líneas guardadas deben sumar el total del presupuesto, no duplicar la última."""
        await CreditService.grant_subscription_credits(test_organization.id, db_session, force=True)

        response = await async_client.post(
            "/api/v1/projects/",
            json={
                "name": "Duplicated Service Project",
                "client_name": "Dup Client",
                "client_email": "dup@example.com",
                "currency": "USD",
                "quote_items": [
                    {
                        "service_id": test_service.id,
                        "estimated_hours": 10.0,
                        "custom_service_name": "Etapa A",
                    },
                    {
                        "service_id": test_service.id,
                        "estimated_hours": 40.0,
                        "custom_service_name": "Etapa B",
                    },
                ],
                "tax_ids": [],
            },
            headers=_auth_headers(owner_user),
        )
        assert response.status_code == 201, response.text
        quote_id = response.json()["id"]

        quote = (await db_session.execute(select(Quote).where(Quote.id == quote_id))).scalar_one()
        items = (
            (await db_session.execute(select(QuoteItem).where(QuoteItem.quote_id == quote_id)))
            .scalars()
            .all()
        )

        assert len(items) == 2
        prices = sorted(Decimal(str(item.client_price)) for item in items)
        costs = sorted(Decimal(str(item.internal_cost)) for item in items)

        # Las dos filas NO pueden ser idénticas: 10h y 40h del mismo servicio.
        assert prices[0] != prices[1], "Ambos ítems quedaron con el precio del último"
        assert costs[0] != costs[1], "Ambos ítems quedaron con el costo del último"

        # Y la suma de las líneas debe cuadrar con el total del presupuesto.
        assert abs(sum(prices, Decimal("0")) - Decimal(str(quote.total_client_price))) < Decimal(
            "1"
        )
        assert abs(sum(costs, Decimal("0")) - Decimal(str(quote.total_internal_cost))) < Decimal(
            "1"
        )


@pytest.mark.integration
class TestAgencyCostHourDecimalHours:
    async def test_endpoint_survives_non_billable_percentage(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        owner_user: User,
        test_organization: Organization,
        test_settings,
    ):
        """
        non_billable_hours_percentage es Numeric: no debe reventar el cálculo de horas.

        Además fija la decisión de producto del 2026-07-27 (H49): el % no facturable NO
        se descuenta de la capacidad, porque `billable_hours_per_week` YA son horas
        facturables (así lo rotula la UI). Este test antes esperaba 110.85, que era el
        resultado de descontar dos veces.
        """
        test_organization.settings = {"primary_currency": "COP"}
        db_session.add(test_organization)

        member = TeamMember(
            name="Dev COP",
            role="Developer",
            salary_monthly_brute=Decimal("8000000"),
            currency="COP",
            billable_hours_per_week=32,
            non_billable_hours_percentage=Decimal("0.2000"),
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(member)
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/settings/calculations/agency-cost-hour",
            headers=_auth_headers(owner_user),
        )
        assert response.status_code == 200, response.text
        payload = response.json()

        # 32 h/semana * 4.33 semanas = 138.56 h/mes. El 0.20 de no facturable NO se aplica:
        # el campo ya es facturable. Descontarlo daba 110.85 e inflaba el BCR un 25%.
        assert float(payload["total_monthly_hours"]) == pytest.approx(138.56, abs=0.05)
        assert Decimal(str(payload["total_monthly_costs"])) > 0
        assert Decimal(str(payload["blended_cost_rate"])) > 0
        assert payload["primary_currency"] == "COP"


@pytest.mark.integration
class TestAiFinancialContextCurrency:
    async def test_primary_currency_is_set_on_the_happy_path(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
    ):
        """El bloque de settings debe correr aunque los proyectos carguen bien."""
        test_organization.settings = {"primary_currency": "COP"}
        db_session.add(test_organization)
        await db_session.commit()

        context = await _build_financial_context_safe(
            db_session, test_organization.id, test_organization
        )

        # Camino feliz: los proyectos cargaron sin excepción...
        assert "projects" in context
        # ...y aun así la moneda quedó resuelta.
        assert context["primary_currency"] == "COP"
