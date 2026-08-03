"""
P2-moneda / H36 + H15: moneda al aplicar un template de industria.

H36: `ApplyTemplateRequest.currency` es un `str` libre (los schemas de cost/team usan
Literal), así que POST /templates/organizations/{id}/apply-template era la única ruta
HTTP por la que un código no soportado entraba crudo a TeamMember.currency y
CostFixed.currency. Después el motor de BCR lo trata como USD: 500.000 CLP se
convierten en 2.000.000.000 COP (~4000x) e inflan el BCR en la misma proporción.

H15: el fix de WI-3 (copiar settings + flag_modified para que el JSON column se
persista) no tenía ningún test; revertirlo dejaba la suite en verde y las orgs sin
`primary_currency`, que es el bug que originó la ronda.
"""

import pytest
from sqlalchemy import func, select

from app.models.cost import CostFixed
from app.models.organization import Organization
from app.models.team import TeamMember
from app.models.template import IndustryTemplate
from app.services.template_service import apply_industry_template


@pytest.fixture
async def branding_template(db_session) -> IndustryTemplate:
    template = IndustryTemplate(
        industry_type="branding_currency_test",
        name="Branding",
        is_active=True,
        suggested_roles=[{"name": "Diseñador", "monthly_cost": 2000, "weekly_hours": 40}],
        suggested_services=[],
        suggested_fixed_costs=[{"name": "Oficina", "amount": 500, "category": "Overhead"}],
    )
    db_session.add(template)
    await db_session.commit()
    return template


async def _count(db_session, model, org_id: int) -> int:
    result = await db_session.execute(
        select(func.count()).select_from(model).where(model.organization_id == org_id)
    )
    return result.scalar_one()


async def _reload_settings(db_session, org_id: int) -> dict:
    """Settings tal como quedaron EN LA BASE (no los del objeto en memoria)."""
    org = await db_session.get(Organization, org_id)
    await db_session.refresh(org)
    return dict(org.settings or {})


@pytest.mark.unit
class TestUnsupportedCurrencyIsRejected:
    async def test_unsupported_currency_raises_before_writing_anything(
        self, db_session, test_organization, branding_template
    ):
        with pytest.raises(ValueError, match="Unsupported currency"):
            await apply_industry_template(
                test_organization.id,
                "branding_currency_test",
                region="COL",
                currency="CLP",
                db=db_session,
            )

        await db_session.rollback()
        assert await _count(db_session, TeamMember, test_organization.id) == 0
        assert await _count(db_session, CostFixed, test_organization.id) == 0

    async def test_currency_is_normalized_to_upper_case(
        self, db_session, test_organization, branding_template
    ):
        await apply_industry_template(
            test_organization.id,
            "branding_currency_test",
            region="COL",
            currency="cop",
            db=db_session,
        )

        members = (
            (
                await db_session.execute(
                    select(TeamMember).where(TeamMember.organization_id == test_organization.id)
                )
            )
            .scalars()
            .all()
        )
        costs = (
            (
                await db_session.execute(
                    select(CostFixed).where(CostFixed.organization_id == test_organization.id)
                )
            )
            .scalars()
            .all()
        )
        assert members and costs
        assert {m.currency for m in members} == {"COP"}
        assert {c.currency for c in costs} == {"COP"}


@pytest.mark.unit
class TestPrimaryCurrencyIsPersisted:
    async def test_apply_template_persists_primary_currency(
        self, db_session, test_organization, branding_template
    ):
        """WI-3: sin la copia del dict + flag_modified, esto vuelve a perderse."""
        await apply_industry_template(
            test_organization.id,
            "branding_currency_test",
            region="COL",
            currency="COP",
            db=db_session,
        )

        settings = await _reload_settings(db_session, test_organization.id)
        assert settings.get("primary_currency") == "COP"
        # Clave legacy en sync, para no dejar settings mixtos.
        assert settings.get("currency") == "COP"
        assert settings.get("template_applied_currency") == "COP"
        assert settings.get("onboarding_completed") is True
        # La config de cargas sociales de Colombia viaja en el mismo dict.
        assert settings["social_charges_config"]["total_percentage"] == 52.852

    async def test_existing_primary_currency_is_not_overwritten(
        self, db_session, test_organization, branding_template
    ):
        """Cambiar la moneda primaria exige normalizar importes; el template no lo hace."""
        test_organization.settings = {"primary_currency": "USD"}
        db_session.add(test_organization)
        await db_session.commit()

        await apply_industry_template(
            test_organization.id,
            "branding_currency_test",
            region="COL",
            currency="COP",
            db=db_session,
        )

        settings = await _reload_settings(db_session, test_organization.id)
        assert settings.get("primary_currency") == "USD"
        assert settings.get("template_applied_currency") == "COP"

    async def test_resolver_agrees_with_what_was_persisted(
        self, db_session, test_organization, branding_template
    ):
        from app.core.currency import resolve_primary_currency

        await apply_industry_template(
            test_organization.id,
            "branding_currency_test",
            region="COL",
            currency="COP",
            db=db_session,
        )
        org = await db_session.get(Organization, test_organization.id)
        await db_session.refresh(org)
        assert resolve_primary_currency(org) == "COP"
