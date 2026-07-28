"""
Unit tests for the canonical primary-currency resolver and exchange-rate handling
ESTÁNDAR NOUGRAM: el dinero nunca pasa por float en las conversiones
"""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.core import currency as currency_module
from app.core.currency import (
    DEFAULT_CURRENCY,
    convert_currency,
    get_exchange_rates_metadata,
    normalize_to_primary_currency,
    resolve_primary_currency,
)
from app.core.money import Money


class TestResolvePrimaryCurrency:
    """Precedence and tolerance of resolve_primary_currency()"""

    def test_primary_currency_wins(self):
        org = SimpleNamespace(
            id=1,
            settings={
                "primary_currency": "COP",
                "currency": "ARS",
                "template_applied_currency": "MXN",
                "country": "USA",
            },
        )
        assert resolve_primary_currency(org) == "COP"

    def test_falls_back_to_legacy_currency_key(self):
        org = SimpleNamespace(id=1, settings={"currency": "ARS", "country": "USA"})
        assert resolve_primary_currency(org) == "ARS"

    def test_falls_back_to_template_applied_currency(self):
        """El caso testigo: org con template COP pero sin primary_currency."""
        org = SimpleNamespace(
            id=5,
            settings={"template_applied_currency": "COP", "template_applied_region": "COL"},
        )
        assert resolve_primary_currency(org) == "COP"

    def test_derives_from_country_when_no_currency_stored(self):
        org = SimpleNamespace(id=5, settings={"country": "COL"})
        assert resolve_primary_currency(org) == "COP"

    def test_derives_from_template_region_when_no_country(self):
        org = SimpleNamespace(id=5, settings={"template_applied_region": "ARG"})
        assert resolve_primary_currency(org) == "ARS"

    def test_invalid_currency_is_ignored(self):
        org = SimpleNamespace(id=1, settings={"primary_currency": "XYZ", "country": "COL"})
        assert resolve_primary_currency(org) == "COP"

    def test_case_and_whitespace_are_normalized(self):
        org = SimpleNamespace(id=1, settings={"primary_currency": " cop "})
        assert resolve_primary_currency(org) == "COP"

    @pytest.mark.parametrize("org", [None, SimpleNamespace(id=1, settings=None)])
    def test_tolerates_missing_org_and_settings(self, org):
        assert resolve_primary_currency(org) == DEFAULT_CURRENCY

    def test_tolerates_empty_settings(self):
        assert resolve_primary_currency(SimpleNamespace(id=1, settings={})) == DEFAULT_CURRENCY

    def test_accepts_bare_settings_mapping(self):
        assert resolve_primary_currency({"primary_currency": "MXN"}) == "MXN"

    def test_accepts_org_shaped_mapping(self):
        assert resolve_primary_currency({"settings": {"primary_currency": "PEN"}}) == "PEN"


class TestSameCurrencyHappyPath:
    """from == to: sin conversión, sin warning, sin pérdida de precisión"""

    def test_decimal_is_returned_untouched(self):
        amount = Decimal("1234567.891234")
        result = convert_currency(amount, "COP", "COP")
        assert isinstance(result, Decimal)
        assert result == amount

    def test_money_is_returned_untouched(self):
        money = Money("1234567.891234", "COP")
        result = convert_currency(money, "COP", "COP")
        assert isinstance(result, Money)
        assert result.amount == money.amount
        assert result.currency == "COP"

    def test_normalize_same_currency_keeps_decimal_precision(self):
        amount = Decimal("999999999.999999")
        result = normalize_to_primary_currency(amount, "COP", "COP")
        assert isinstance(result, Decimal)
        assert result == amount

    def test_same_currency_emits_no_placeholder_warning(self, monkeypatch):
        warnings: list[tuple] = []
        monkeypatch.setattr(currency_module, "_WARNED_PLACEHOLDER_PAIRS", set())
        monkeypatch.setattr(currency_module, "EXCHANGE_RATES_ARE_PLACEHOLDER", True)
        monkeypatch.setattr(
            currency_module.logger,
            "warning",
            lambda *args, **kwargs: warnings.append((args, kwargs)),
        )

        convert_currency(Decimal("100"), "COP", "COP")

        assert warnings == []

    def test_case_insensitive_same_currency_is_still_a_no_op(self):
        amount = Decimal("100.123456")
        assert convert_currency(amount, "cop", "COP") == amount


class TestPlaceholderRateWarning:
    """Warning de tasas placeholder: una sola vez por par de monedas"""

    def test_warns_once_per_currency_pair(self, monkeypatch):
        warnings: list[tuple] = []
        monkeypatch.setattr(currency_module, "_WARNED_PLACEHOLDER_PAIRS", set())
        monkeypatch.setattr(currency_module, "EXCHANGE_RATES_ARE_PLACEHOLDER", True)
        monkeypatch.setattr(
            currency_module.logger,
            "warning",
            lambda *args, **kwargs: warnings.append((args, kwargs)),
        )

        convert_currency(Decimal("100"), "COP", "USD")
        convert_currency(Decimal("200"), "COP", "USD")
        convert_currency(Decimal("300"), "USD", "COP")

        assert len(warnings) == 2

    def test_no_warning_when_rates_are_not_placeholder(self, monkeypatch):
        warnings: list[tuple] = []
        monkeypatch.setattr(currency_module, "_WARNED_PLACEHOLDER_PAIRS", set())
        monkeypatch.setattr(currency_module, "EXCHANGE_RATES_ARE_PLACEHOLDER", False)
        monkeypatch.setattr(
            currency_module.logger,
            "warning",
            lambda *args, **kwargs: warnings.append((args, kwargs)),
        )

        convert_currency(Decimal("100"), "COP", "USD")

        assert warnings == []


class TestExchangeRatesMetadata:
    """Las tasas deben ser auditables: fecha y origen expuestos"""

    def test_metadata_exposes_as_of_and_source(self):
        metadata = get_exchange_rates_metadata()
        assert metadata["as_of"]
        assert metadata["source"]
        assert isinstance(metadata["is_placeholder"], bool)
        assert metadata["rates_to_usd"]["USD"] == "1"

    def test_cross_currency_conversion_uses_configured_rates(self):
        converted = convert_currency(Decimal("4000"), "COP", "USD")
        assert converted == Decimal("1")
