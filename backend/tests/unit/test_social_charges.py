"""
Recargo patronal (cargas sociales): una sola implementación.

El bug histórico: había cuatro copias del cálculo del multiplicador y dos de ellas
sumaban el desglose ignorando `total_percentage`. Con la config real de la org 5
(total_percentage=52.852, desglose que suma 25.192) el mismo endpoint se contradecía
a sí mismo: el BCR usaba 1.52852 y los salarios que reportaba usaban 1.25192.
"""

from decimal import Decimal

import pytest

from app.core.social_charges import (
    resolve_social_charges_multiplier,
    resolve_social_charges_percentage,
)

# Config real de la org testigo: el total NO coincide con la suma del desglose.
ORG5_CONFIG = {
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


@pytest.mark.unit
class TestResolveSocialChargesMultiplier:
    def test_total_percentage_wins_over_breakdown(self):
        """total_percentage es la fuente de verdad; el desglose es informativo."""
        assert resolve_social_charges_multiplier(ORG5_CONFIG) == Decimal("1.52852")
        assert resolve_social_charges_percentage(ORG5_CONFIG) == Decimal("52.852")

    def test_breakdown_is_legacy_fallback_when_total_missing(self):
        config = dict(ORG5_CONFIG)
        config.pop("total_percentage")
        # 8.5 + 12.0 + 0.522 + 4.17 = 25.192
        assert resolve_social_charges_multiplier(config) == Decimal("1.25192")

    def test_breakdown_is_legacy_fallback_when_total_is_zero(self):
        config = dict(ORG5_CONFIG, total_percentage=0)
        assert resolve_social_charges_multiplier(config) == Decimal("1.25192")

    def test_disabled_returns_neutral_multiplier(self):
        config = dict(ORG5_CONFIG, enable_social_charges=False)
        assert resolve_social_charges_multiplier(config) == Decimal("1.0")

    def test_missing_config_returns_neutral_multiplier(self):
        assert resolve_social_charges_multiplier(None) == Decimal("1.0")
        assert resolve_social_charges_multiplier({}) == Decimal("1.0")

    def test_none_values_do_not_break_the_sum(self):
        config = {
            "enable_social_charges": True,
            "total_percentage": None,
            "health_percentage": None,
            "pension_percentage": 10,
        }
        assert resolve_social_charges_multiplier(config) == Decimal("1.10")

    def test_returns_decimal_not_float(self):
        result = resolve_social_charges_multiplier(ORG5_CONFIG)
        assert isinstance(result, Decimal)
