"""
P2-moneda / H09 + H17: validación de las tasas de cambio configurables.

Antes de este arreglo:
  - EXCHANGE_RATES_TO_USD='{"COP": "4.150,00"}' hacía que `import app.core.currency`
    reventara con decimal.InvalidOperation y la app no arrancaba.
  - '{"COP": "0"}' arrancaba bien y después lanzaba DivisionByZero en la primera
    conversión.
  - '{"COP": "-4150"}' invertía el signo de todos los importes convertidos.
  - una moneda desconocida devolvía tasa 1 sin ningún log, indistinguible de una
    paridad real 1:1 con el dólar.
"""

import logging
from decimal import Decimal

import pytest

from app.core.config import DEFAULT_EXCHANGE_RATES_TO_USD, parse_exchange_rate
from app.core.config import settings as app_settings
from app.core.currency import (
    _WARNED_UNKNOWN_CURRENCIES,
    _build_rates_to_usd,
    get_exchange_rate_to_usd,
    normalize_to_primary_currency,
)


@pytest.mark.unit
class TestParseExchangeRate:
    @pytest.mark.parametrize(
        "value",
        [
            "4.150,00",  # formato es-CO: rompía el arranque del proceso
            "abc",
            "",
            "0",  # división por cero aguas abajo
            "-4150",  # signo invertido, sin ninguna alarma
            "NaN",
            "Infinity",
            None,
        ],
    )
    def test_invalid_values_are_rejected(self, value):
        assert parse_exchange_rate("COP", value) is None

    def test_valid_value_is_parsed_as_decimal(self):
        parsed = parse_exchange_rate("COP", "4150")
        assert parsed == Decimal("4150")
        assert isinstance(parsed, Decimal)


@pytest.mark.unit
class TestSettingsOverrideIsValidated:
    def _rates_with_override(self, raw: str) -> dict[str, str]:
        return app_settings.model_copy(
            update={"EXCHANGE_RATES_TO_USD": raw}
        ).exchange_rates_to_usd_dict

    @pytest.mark.parametrize("raw_value", ['"4.150,00"', '"0"', '"-4150"', '"abc"'])
    def test_bad_override_keeps_the_default_rate(self, raw_value):
        rates = self._rates_with_override(f'{{"COP": {raw_value}}}')
        assert rates["COP"] == DEFAULT_EXCHANGE_RATES_TO_USD["COP"]

    def test_good_override_wins(self):
        rates = self._rates_with_override('{"cop": "4150"}')
        assert rates["COP"] == "4150"

    def test_bad_entry_does_not_drop_the_good_ones(self):
        rates = self._rates_with_override('{"COP": "0", "ARS": "1200"}')
        assert rates["ARS"] == "1200"
        assert rates["COP"] == DEFAULT_EXCHANGE_RATES_TO_USD["COP"]


@pytest.mark.unit
class TestBuildRatesToUsd:
    def test_invalid_entries_fall_back_to_defaults_instead_of_raising(self):
        rates = _build_rates_to_usd({"COP": "4.150,00", "ARS": "0", "MXN": "-17"})
        assert rates["COP"] == Decimal(DEFAULT_EXCHANGE_RATES_TO_USD["COP"])
        assert rates["ARS"] == Decimal(DEFAULT_EXCHANGE_RATES_TO_USD["ARS"])
        assert rates["MXN"] == Decimal(DEFAULT_EXCHANGE_RATES_TO_USD["MXN"])

    def test_every_rate_is_strictly_positive(self):
        rates = _build_rates_to_usd({"COP": "0"})
        assert all(rate > 0 for rate in rates.values())

    def test_usd_base_is_always_present(self):
        assert _build_rates_to_usd({"USD": "0"})["USD"] == Decimal("1")


@pytest.mark.unit
class TestUnknownCurrencyIsLogged:
    def test_unknown_code_warns_once(self, caplog):
        _WARNED_UNKNOWN_CURRENCIES.discard("CLP")
        with caplog.at_level(logging.WARNING, logger="app.core.currency"):
            assert get_exchange_rate_to_usd("CLP") == Decimal("1")
            get_exchange_rate_to_usd("CLP")
        warnings = [r for r in caplog.records if "Unsupported currency" in r.getMessage()]
        assert len(warnings) == 1, "debe advertir exactamente una vez por código"
        assert "CLP" in _WARNED_UNKNOWN_CURRENCIES

    def test_known_code_does_not_warn(self, caplog):
        with caplog.at_level(logging.WARNING, logger="app.core.currency"):
            assert get_exchange_rate_to_usd("COP") > 0
        assert not [r for r in caplog.records if "Unsupported currency" in r.getMessage()]

    def test_normalize_warns_when_an_unsupported_code_is_silently_swapped(self, caplog):
        """H36: 500.000 CLP entrando a una org COP no puede pasar sin ruido."""
        _WARNED_UNKNOWN_CURRENCIES.discard("CLP")
        with caplog.at_level(logging.WARNING, logger="app.core.currency"):
            normalize_to_primary_currency(Decimal("500000"), "CLP", "COP")
        assert [r for r in caplog.records if "Unsupported currency" in r.getMessage()]

    def test_empty_currency_is_not_reported_as_unsupported(self, caplog):
        with caplog.at_level(logging.WARNING, logger="app.core.currency"):
            normalize_to_primary_currency(Decimal("100"), None, "COP")
        assert not [r for r in caplog.records if "Unsupported currency" in r.getMessage()]
