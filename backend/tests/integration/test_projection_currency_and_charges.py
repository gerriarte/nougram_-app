"""
P2-moneda / H37 + H31: proyecciones que se contradecían con el resto del motor.

H37: annual_sales_projection_service era el último call site con una copia inline
del multiplicador de cargas sociales (`total_percentage` sin fallback al desglose y
sin `or 0`). Sesenta líneas más arriba, la MISMA función pide el BCR a
calculate_blended_cost_rate, que sí usa el resolver canónico. Resultado: el punto de
equilibrio salía sin recargo patronal (~46,9% menos sobre los sueldos) en el mismo
payload cuyo BCR sí lo incluía; y con `total_percentage: None` reventaba entero
(Decimal("None") -> InvalidOperation).

H31: POST /sales/projection tomaba la moneda del body con default "USD". No es una
etiqueta: es el TARGET de normalización del BCR, así que una org COP recibía todos
sus costos divididos por 4000 y una proyección en dólares perfectamente plausible.
"""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.core.social_charges import resolve_social_charges_multiplier
from app.models.annual_sales_projection import (
    AnnualSalesProjection,
    AnnualSalesProjectionEntry,
)
from app.models.organization import Organization
from app.models.service import Service
from app.models.team import TeamMember
from app.models.user import User
from app.services.annual_sales_projection_service import calculate_projection_summary

# Desglose colombiano completo, SIN `total_percentage`. No es un fósil: el campo es
# opcional en SocialChargesConfig, así que mandando solo enable_social_charges=true
# a PUT /settings se crea exactamente esta forma hoy.
LEGACY_SOCIAL_CONFIG_WITHOUT_TOTAL = {
    "enable_social_charges": True,
    "health_percentage": 8.5,
    "pension_percentage": 12.0,
    "arl_percentage": 0.522,
    "parafiscales_percentage": 4.0,
    "prima_services_percentage": 8.33,
    "cesantias_percentage": 8.33,
    "int_cesantias_percentage": 1.0,
    "vacations_percentage": 4.17,
}

MONTHLY_SALARY_COP = Decimal("1000000")


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
async def cop_user(db_session: AsyncSession, test_organization: Organization) -> User:
    user = User(
        email=f"proj-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Projection User",
        role="owner",
        role_type="tenant",
        hashed_password=get_password_hash("password123"),
        organization_id=test_organization.id,
    )
    db_session.add(user)
    db_session.add(
        TeamMember(
            name="Dev COP",
            role="Developer",
            salary_monthly_brute=MONTHLY_SALARY_COP,
            currency="COP",
            billable_hours_per_week=40,
            non_billable_hours_percentage=Decimal("0"),
            apply_social_charges=True,
            is_active=True,
            organization_id=test_organization.id,
        )
    )
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _make_cop_org(
    db_session: AsyncSession, org: Organization, social_config: dict | None
) -> Organization:
    org.settings = {"primary_currency": "COP", "social_charges_config": social_config}
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


async def _make_projection(
    db_session: AsyncSession, org: Organization, user: User, service: Service
) -> AnnualSalesProjection:
    projection = AnnualSalesProjection(
        organization_id=org.id, year=2026, is_active=True, created_by_id=user.id
    )
    db_session.add(projection)
    await db_session.commit()
    await db_session.refresh(projection)

    db_session.add(
        AnnualSalesProjectionEntry(
            projection_id=projection.id,
            service_id=service.id,
            month=1,
            quantity=1,
            hours_per_unit=10.0,
        )
    )
    await db_session.commit()
    await db_session.refresh(projection)
    return projection


@pytest.mark.integration
class TestAnnualProjectionUsesTheCanonicalSocialCharges:
    async def test_legacy_config_without_total_percentage_still_applies_the_breakdown(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_service: Service,
        cop_user: User,
    ):
        org = await _make_cop_org(
            db_session, test_organization, dict(LEGACY_SOCIAL_CONFIG_WITHOUT_TOTAL)
        )
        projection = await _make_projection(db_session, org, cop_user, test_service)

        summary = await calculate_projection_summary(projection, db_session)

        multiplier = resolve_social_charges_multiplier(LEGACY_SOCIAL_CONFIG_WITHOUT_TOTAL)
        assert multiplier == Decimal("1.46852")
        expected = MONTHLY_SALARY_COP * multiplier
        # Antes: 1.000.000 exactos, es decir el break-even sin ningún recargo patronal.
        assert Decimal(str(summary["break_even_monthly_cost"])) == expected

    async def test_total_percentage_none_does_not_crash_the_endpoint(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_service: Service,
        cop_user: User,
    ):
        config = {**LEGACY_SOCIAL_CONFIG_WITHOUT_TOTAL, "total_percentage": None}
        org = await _make_cop_org(db_session, test_organization, config)
        projection = await _make_projection(db_session, org, cop_user, test_service)

        # Antes: decimal.InvalidOperation por Decimal(str(None)) == Decimal("None").
        summary = await calculate_projection_summary(projection, db_session)

        expected = MONTHLY_SALARY_COP * resolve_social_charges_multiplier(config)
        assert Decimal(str(summary["break_even_monthly_cost"])) == expected

    async def test_disabled_social_charges_keep_the_raw_payroll(
        self,
        db_session: AsyncSession,
        test_organization: Organization,
        test_service: Service,
        cop_user: User,
    ):
        org = await _make_cop_org(db_session, test_organization, {"enable_social_charges": False})
        projection = await _make_projection(db_session, org, cop_user, test_service)

        summary = await calculate_projection_summary(projection, db_session)
        assert Decimal(str(summary["break_even_monthly_cost"])) == MONTHLY_SALARY_COP


@pytest.mark.integration
class TestSalesProjectionUsesTheOrganizationCurrency:
    async def test_omitted_currency_uses_the_primary_currency(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
        test_service: Service,
        cop_user: User,
    ):
        await _make_cop_org(db_session, test_organization, None)

        response = await async_client.post(
            "/api/v1/sales/projection",
            headers=_auth_headers(cop_user),
            json={
                "service_ids": [test_service.id],
                "estimated_hours_per_service": {str(test_service.id): 40.0},
                "period_months": 12,
            },
        )

        assert response.status_code == 200, response.text
        # Antes el body defaulteaba a "USD" y el BCR de una org COP salía dividido por 4000.
        assert response.json()["currency"] == "COP"

    async def test_currency_that_disagrees_with_the_org_is_rejected(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
        test_service: Service,
        cop_user: User,
    ):
        await _make_cop_org(db_session, test_organization, None)

        response = await async_client.post(
            "/api/v1/sales/projection",
            headers=_auth_headers(cop_user),
            json={
                "service_ids": [test_service.id],
                "estimated_hours_per_service": {str(test_service.id): 40.0},
                "currency": "USD",
            },
        )

        assert response.status_code == 400, response.text
        assert "primary currency" in response.json()["detail"]

    async def test_matching_currency_is_accepted(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
        test_service: Service,
        cop_user: User,
    ):
        await _make_cop_org(db_session, test_organization, None)

        response = await async_client.post(
            "/api/v1/sales/projection",
            headers=_auth_headers(cop_user),
            json={
                "service_ids": [test_service.id],
                "estimated_hours_per_service": {str(test_service.id): 40.0},
                "currency": "cop",
            },
        )

        assert response.status_code == 200, response.text
        assert response.json()["currency"] == "COP"

    async def test_unsupported_currency_is_rejected(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_organization: Organization,
        test_service: Service,
        cop_user: User,
    ):
        await _make_cop_org(db_session, test_organization, None)

        response = await async_client.post(
            "/api/v1/sales/projection",
            headers=_auth_headers(cop_user),
            json={
                "service_ids": [test_service.id],
                "estimated_hours_per_service": {str(test_service.id): 40.0},
                "currency": "CLP",
            },
        )

        assert response.status_code == 400, response.text
        assert "Unsupported currency" in response.json()["detail"]
