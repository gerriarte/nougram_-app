"""
Paquete P4-bcr-cargas: regresiones del motor de BCR y de cargas sociales.

H39 - la clave de caché del BCR solo hasheaba `total_percentage`: con una config legacy
      (sin total, resuelta por el desglose) editar un concepto no invalidaba la entrada.
H51/H34 - `social_charges_config` era código muerto que solo desalineaba la clave: la lectura
      usaba el parámetro y la escritura releía la DB, así que un caller que no pasaba config
      nunca acertaba su propia entrada (miss permanente + 2 SELECT extra por llamada).
H35/H41 - la única división del BCR degradaba el divisor a float.
H40 - divergencia silenciosa entre `total_percentage` y el desglose por concepto.
"""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import social_charges as social_charges_module
from app.core.calculations import calculate_blended_cost_rate
from app.core.money import Money
from app.core.social_charges import resolve_social_charges_percentage
from app.models.cost import CostFixed
from app.models.organization import Organization
from app.models.team import TeamMember

# Config legacy: sin total_percentage, el multiplicador sale del desglose.
LEGACY_CONFIG = {
    "enable_social_charges": True,
    "health_percentage": 8.5,
    "pension_percentage": 12.0,
}

# Preset CO real (frontend/src/lib/social-charges-presets.ts): el desglose es informativo y
# NO cuadra con el total por diseño (52.852 vs 46.852).
CO_PRESET_CONFIG = {
    "enable_social_charges": True,
    "total_percentage": 52.852,
    "health_percentage": 8.5,
    "pension_percentage": 12.0,
    "arl_percentage": 0.522,
    "parafiscales_percentage": 4.0,
    "prima_services_percentage": 8.33,
    "cesantias_percentage": 8.33,
    "int_cesantias_percentage": 1.0,
    "vacations_percentage": 4.17,
}

# Config de la org 5 en producción: total 52.852 contra un desglose de 25.192.
ORG5_DIVERGENT_CONFIG = {
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


@pytest.fixture(autouse=True)
def _clear_cache():
    from app.core.cache import get_cache

    get_cache().clear()
    yield
    get_cache().clear()


@pytest.fixture
async def org_with_costs(db_session: AsyncSession, test_organization: Organization):
    """Org COP con 1 sueldo y 1 costo fijo; las cargas se setean por test."""
    db_session.add(
        CostFixed(
            name="Overhead",
            amount_monthly=Decimal("1000000"),
            currency="COP",
            category="Overhead",
            organization_id=test_organization.id,
        )
    )
    db_session.add(
        TeamMember(
            name="Dev",
            role="Developer",
            salary_monthly_brute=Decimal("4000000"),
            currency="COP",
            billable_hours_per_week=40,
            non_billable_hours_percentage=Decimal("0"),
            is_active=True,
            organization_id=test_organization.id,
        )
    )
    await db_session.commit()
    return test_organization


@pytest.mark.unit
class TestBlendedCostRateCache:
    async def test_breakdown_change_invalidates_cache_on_legacy_config(
        self, db_session: AsyncSession, org_with_costs: Organization
    ):
        """H39: sin total_percentage el desglose ES el cálculo, así que tiene que entrar a la clave.

        El caller pasa la config legacy además de tenerla persistida, que es donde el bug
        realmente muerde: con el código viejo la clave de LECTURA salía del parámetro
        (`total_percentage` ausente -> ':social_0') y la de ESCRITURA de la config releída de la
        DB (misma config legacy -> también ':social_0'). Ambas colapsaban, así que la segunda
        llamada acertaba la entrada de la primera y devolvía el BCR calculado con el 20.5% viejo.
        Si el test NO pasara la config, la clave de lectura quedaría sin sufijo y la de escritura
        con ':social_0': miss permanente, recálculo siempre y el valor rancio nunca aparecería.
        """
        org_with_costs.settings = {
            "primary_currency": "COP",
            "social_charges_config": dict(LEGACY_CONFIG),
        }
        db_session.add(org_with_costs)
        await db_session.commit()

        first = await calculate_blended_cost_rate(
            db_session,
            primary_currency="COP",
            tenant_id=org_with_costs.id,
            social_charges_config=dict(LEGACY_CONFIG),
        )

        # El usuario corrige pensión 12 -> 16 (total_percentage sigue ausente).
        updated = dict(LEGACY_CONFIG)
        updated["pension_percentage"] = 16.0
        org_with_costs.settings = {
            "primary_currency": "COP",
            "social_charges_config": updated,
        }
        db_session.add(org_with_costs)
        await db_session.commit()

        second = await calculate_blended_cost_rate(
            db_session,
            primary_currency="COP",
            tenant_id=org_with_costs.id,
            social_charges_config=updated,
        )

        # Antes: misma clave ':social_0' -> durante 300 s se seguía cotizando con 20.5%.
        expected_first = (Decimal("4000000") * Decimal("1.205") + Decimal("1000000")) / (
            Decimal("40") * Decimal("4.33")
        )
        expected_second = (Decimal("4000000") * Decimal("1.245") + Decimal("1000000")) / (
            Decimal("40") * Decimal("4.33")
        )
        assert abs(first - expected_first) < Decimal("1")
        # El código viejo devolvía acá el valor rancio (== first, salvo round-trip por float).
        assert abs(second - expected_second) < Decimal("1"), (
            f"BCR rancio: se esperaba ~{expected_second} (24.5%) y llegó {second}"
        )
        assert second - first > Decimal("900")

    async def test_caller_without_config_hits_its_own_cache_entry(
        self, db_session: AsyncSession, org_with_costs: Organization
    ):
        """H51/H34: leer y escribir con la misma clave; sin config pasada también."""
        org_with_costs.settings = {
            "primary_currency": "COP",
            "social_charges_config": dict(ORG5_DIVERGENT_CONFIG),
        }
        db_session.add(org_with_costs)
        await db_session.commit()

        first = await calculate_blended_cost_rate(
            db_session, primary_currency="COP", tenant_id=org_with_costs.id
        )

        # Cambia un dato del cálculo sin tocar las cargas: si la entrada escrita es la que se
        # lee, el resultado no puede moverse dentro del TTL.
        db_session.add(
            CostFixed(
                name="Overhead 2",
                amount_monthly=Decimal("9000000"),
                currency="COP",
                category="Overhead",
                organization_id=org_with_costs.id,
            )
        )
        await db_session.commit()

        second = await calculate_blended_cost_rate(
            db_session, primary_currency="COP", tenant_id=org_with_costs.id
        )
        # Antes: leía 'blended_cost_rate:COP:tenant_N' y escribía '...:social_52.852' -> miss
        # permanente, recálculo completo en cada llamada (second = first + 9.000.000/173,2).
        # (la tolerancia es el round-trip por float con el que se cachea el valor)
        assert abs(second - first) < Decimal("0.001")

    async def test_passed_config_overrides_stored_one(
        self, db_session: AsyncSession, org_with_costs: Organization
    ):
        """El parámetro social_charges_config ahora simula de verdad (antes era decorativo)."""
        org_with_costs.settings = {"primary_currency": "COP"}
        db_session.add(org_with_costs)
        await db_session.commit()

        simulated = await calculate_blended_cost_rate(
            db_session,
            primary_currency="COP",
            tenant_id=org_with_costs.id,
            social_charges_config={"enable_social_charges": True, "total_percentage": 50},
        )
        expected = (Decimal("4000000") * Decimal("1.5") + Decimal("1000000")) / (
            Decimal("40") * Decimal("4.33")
        )
        assert abs(simulated - expected) < Decimal("1")


@pytest.mark.unit
class TestBlendedCostRateUsesDecimalDivision:
    async def test_divisor_is_decimal(
        self, db_session: AsyncSession, org_with_costs: Organization, monkeypatch
    ):
        """H35/H41: ESTÁNDAR NOUGRAM — la división del BCR no pasa por float."""
        seen: list[type] = []
        original_divide = Money.divide

        def spy(self, divisor):
            seen.append(type(divisor))
            return original_divide(self, divisor)

        monkeypatch.setattr(Money, "divide", spy)

        await calculate_blended_cost_rate(
            db_session, primary_currency="COP", tenant_id=org_with_costs.id, use_cache=False
        )

        assert seen, "el BCR no llamó a Money.divide"
        assert all(t is Decimal for t in seen), f"divisor degradado a {seen}"


@pytest.mark.unit
class TestSocialChargesDivergenceIsReported:
    def test_warns_when_total_and_breakdown_tell_different_stories(self, monkeypatch):
        """H40: 52.852 declarado vs 25.192 en el desglose no puede resolverse en silencio."""
        captured: list[tuple] = []
        social_charges_module._WARNED_BREAKDOWN_DIVERGENCES.clear()
        monkeypatch.setattr(
            social_charges_module.logger,
            "warning",
            lambda message, **kwargs: captured.append((message, kwargs)),
        )

        percentage = resolve_social_charges_percentage(ORG5_DIVERGENT_CONFIG)

        # La precedencia no cambia: total_percentage sigue siendo la fuente de verdad.
        assert percentage == Decimal("52.852")
        assert captured, "no se emitió ninguna señal ante el desvío"
        assert captured[0][1]["breakdown_sum"] == "25.192"

        # Deduplicado: el mismo desvío no repite el aviso en cada sueldo de cada cálculo.
        resolve_social_charges_percentage(ORG5_DIVERGENT_CONFIG)
        assert len(captured) == 1

    def test_does_not_warn_for_the_co_preset(self, monkeypatch):
        """El desglose del preset CO es informativo: avisar ahí sería ruido permanente."""
        captured: list[tuple] = []
        social_charges_module._WARNED_BREAKDOWN_DIVERGENCES.clear()
        monkeypatch.setattr(
            social_charges_module.logger,
            "warning",
            lambda message, **kwargs: captured.append((message, kwargs)),
        )

        assert resolve_social_charges_percentage(CO_PRESET_CONFIG) == Decimal("52.852")
        assert captured == []
