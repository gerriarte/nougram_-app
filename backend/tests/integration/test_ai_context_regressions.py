"""
Regresiones del paquete P5-ia (contexto financiero que se le entrega a la IA
y rutas de importación que persisten moneda).

H38 - El "Blended Cost Rate" del prompt era costos_fijos / horas: sin nómina,
      sin cargas sociales y sin amortización (~4x por debajo del real).
H22 - Los costos fijos se sumaban sin normalizar la moneda por fila y después
      el prompt rotulaba el total con la moneda primaria.
H21 - La moneda del prompt salía de `agency_settings`, tabla GLOBAL sin
      organization_id: un tenant heredaba la moneda de otro.
H16 - Las importaciones (parse de documentos IA y Google Sheets) defaulteaban
      la moneda a "USD" en vez de a la primaria de la organización.
"""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.ai import _build_financial_context_safe
from app.core.calculations import calculate_blended_cost_rate
from app.core.security import create_access_token, get_password_hash
from app.core.sheets import resolve_import_currency, row_currency
from app.models.cost import CostFixed
from app.models.organization import Organization
from app.models.settings import AgencySettings
from app.models.team import TeamMember
from app.models.user import User
from app.services.ai_service import ai_service

SOCIAL_CONFIG_CO = {
    "enable_social_charges": True,
    "total_percentage": 52.852,
}
SOCIAL_MULTIPLIER = Decimal("1.52852")
FIXED_COSTS = Decimal("2275050")
SALARY = Decimal("4004500")
MONTHLY_HOURS = Decimal("40") * Decimal("4.33")


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
async def cop_org(db_session: AsyncSession, test_organization: Organization) -> Organization:
    """Org en COP con 1 costo fijo y 1 sueldo, ambos en COP."""
    test_organization.settings = {
        "primary_currency": "COP",
        "social_charges_config": dict(SOCIAL_CONFIG_CO),
    }
    db_session.add(test_organization)
    db_session.add(
        CostFixed(
            name="Overhead COP",
            amount_monthly=FIXED_COSTS,
            currency="COP",
            category="Overhead",
            organization_id=test_organization.id,
        )
    )
    db_session.add(
        TeamMember(
            name="Dev COP",
            role="Developer",
            salary_monthly_brute=SALARY,
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


@pytest.fixture
async def cop_owner(db_session: AsyncSession, cop_org: Organization) -> User:
    user = User(
        email=f"ai-owner-{uuid.uuid4().hex[:8]}@example.com",
        full_name="AI Owner",
        role="owner",
        role_type="tenant",
        hashed_password=get_password_hash("password123"),
        organization_id=cop_org.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.integration
class TestAiBlendedCostRateIsCanonical:
    async def test_bcr_includes_payroll_and_social_charges(
        self, db_session: AsyncSession, cop_org: Organization
    ):
        """H38: el BCR del prompt debe ser el canónico, no overhead/horas."""
        context = await _build_financial_context_safe(db_session, cop_org.id, cop_org)

        canonical = await calculate_blended_cost_rate(
            db_session, primary_currency="COP", use_cache=False, tenant_id=cop_org.id
        )
        overhead_only = round(FIXED_COSTS / MONTHLY_HOURS, 2)  # 13.135,39: el valor viejo

        reported = Decimal(str(context["blended_cost_rate"]))
        assert abs(reported - canonical) < Decimal("1"), (
            "El BCR del contexto de IA debe salir de calculate_blended_cost_rate"
        )
        # (2.275.050 + 4.004.500 * 1,52852) / 173,20 = 48.475,80
        expected = (FIXED_COSTS + SALARY * SOCIAL_MULTIPLIER) / MONTHLY_HOURS
        assert abs(reported - expected) < Decimal("1")
        assert reported > overhead_only * 3, "El valor viejo era ~3,7x más barato"

    async def test_context_exposes_payroll_and_total_agency_cost(
        self, db_session: AsyncSession, cop_org: Organization
    ):
        """H22: el prompt informaba sólo costos fijos como 'costo de la agencia'."""
        context = await _build_financial_context_safe(db_session, cop_org.id, cop_org)

        payroll = Decimal(str(context["total_monthly_payroll"]))
        total = Decimal(str(context["total_monthly_agency_costs"]))

        assert abs(payroll - SALARY * SOCIAL_MULTIPLIER) < Decimal("1")
        assert abs(total - (FIXED_COSTS + SALARY * SOCIAL_MULTIPLIER)) < Decimal("1")

    async def test_prompt_renders_the_new_cost_block(self, cop_org: Organization):
        prompt = ai_service._build_financial_prompt(
            {
                "primary_currency": "COP",
                "total_monthly_costs": Decimal("2275050"),
                "total_monthly_payroll": Decimal("6121"),
                "total_monthly_agency_costs": Decimal("2281171"),
                "blended_cost_rate": Decimal("48475.80"),
                "team_size": 1,
                "total_monthly_hours": Decimal("173.20"),
                "projects": [],
                "services": [],
            }
        )
        assert "Nómina mensual" in prompt
        assert "48,475.80 COP/hora" in prompt


@pytest.mark.integration
class TestAiContextNormalizesCurrencies:
    async def test_fixed_costs_in_another_currency_are_converted(
        self, db_session: AsyncSession, cop_org: Organization
    ):
        """H22: un SaaS en USD no puede sumarse crudo a un alquiler en COP."""
        db_session.add(
            CostFixed(
                name="SaaS USD",
                amount_monthly=Decimal("100"),
                currency="USD",
                category="Software",
                organization_id=cop_org.id,
            )
        )
        await db_session.commit()

        context = await _build_financial_context_safe(db_session, cop_org.id, cop_org)
        total = Decimal(str(context["total_monthly_costs"]))

        # Sin normalizar daba 2.275.150 (100 USD sumados como 100 COP).
        assert total > FIXED_COSTS + Decimal("1000"), (
            "Los 100 USD deben convertirse a COP antes de sumarse"
        )
        assert context["primary_currency"] == "COP"


@pytest.mark.integration
class TestAiContextCurrencyIsTenantScoped:
    async def test_global_agency_settings_row_does_not_leak_into_the_tenant(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """H21: agency_settings no tiene organization_id; no puede fijar la moneda."""
        db_session.add(AgencySettings(primary_currency="COP", currency_symbol="$"))
        test_organization.settings = None
        db_session.add(test_organization)
        await db_session.commit()
        await db_session.refresh(test_organization)

        context = await _build_financial_context_safe(
            db_session, test_organization.id, test_organization
        )

        # Antes: leía la fila global y devolvía 'COP' (moneda de otro tenant).
        assert context["primary_currency"] == "USD"


@pytest.mark.integration
class TestImportCurrencyDefaults:
    async def test_sheets_import_defaults_to_org_primary_currency(
        self, db_session: AsyncSession, cop_org: Organization
    ):
        """H16: la sync de Google Sheets creaba TeamMember/CostFixed en USD."""
        assert await resolve_import_currency(db_session, cop_org.id) == "COP"

    async def test_sheets_row_currency_only_accepts_supported_codes(self):
        assert row_currency({"currency": "cop"}) == "COP"
        assert row_currency({"currency": " "}) is None
        assert row_currency({}) is None
        # Un código no soportado se descarta: guardarlo crudo equivale a USD.
        assert row_currency({"currency": "CLP"}) is None

    async def test_parse_document_defaults_to_org_primary_currency(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        cop_org: Organization,
        cop_owner: User,
        monkeypatch,
    ):
        """H16: el preview de /ai/parse-document rotulaba todo como USD."""

        async def fake_parse(text: str, document_type: str | None = None) -> dict:
            return {
                "success": True,
                "data": {
                    "team_members": [
                        {
                            "name": "Diseñadora",
                            "role": "Designer",
                            "salary_monthly_brute": 6000000,
                            "billable_hours_per_week": 40,
                        }
                    ],
                    "fixed_costs": [
                        {
                            "name": "Alquiler",
                            "amount_monthly": 2275050,
                            "category": "Overhead",
                        }
                    ],
                    "subscriptions": [],
                    "confidence_scores": {},
                    "warnings": [],
                },
            }

        monkeypatch.setattr(ai_service, "client", object())
        monkeypatch.setattr(ai_service, "parse_unstructured_data", fake_parse)

        response = await async_client.post(
            "/api/v1/ai/parse-document",
            json={"text": "Nomina de la agencia", "document_type": "mixed"},
            headers=_auth_headers(cop_owner),
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["team_members"][0]["currency"] == "COP"
        assert payload["fixed_costs"][0]["currency"] == "COP"

    async def test_sheets_import_currency_falls_back_without_org(self, db_session: AsyncSession):
        assert await resolve_import_currency(db_session, None) == "USD"

        result = await db_session.execute(select(Organization).where(Organization.id == -1))
        assert result.scalar_one_or_none() is None
        assert await resolve_import_currency(db_session, -1) == "USD"
