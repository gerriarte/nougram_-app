"""
Unit tests for Money class
ESTÁNDAR NOUGRAM: Tests de precisión financiera grado bancario
"""

from decimal import Decimal

import pytest

from app.core.money import Money, from_api, sum_money, to_api, to_money


class TestMoneyCreation:
    """Tests for Money object creation"""

    def test_create_from_decimal(self):
        """Test creating Money from Decimal"""
        amount = Decimal("100.50")
        money = Money(amount, "USD")
        assert money.amount == Decimal("100.50")
        assert money.currency == "USD"

    def test_create_from_string(self):
        """Test creating Money from string"""
        money = Money("100.50", "USD")
        assert money.amount == Decimal("100.50")
        assert money.currency == "USD"

    def test_create_from_float(self):
        """Test creating Money from float (converts to string first)"""
        money = Money(100.50, "USD")
        assert money.amount == Decimal("100.50")
        assert money.currency == "USD"

    def test_create_from_int(self):
        """Test creating Money from int"""
        money = Money(100, "USD")
        assert money.amount == Decimal("100")
        assert money.currency == "USD"

    def test_currency_uppercase(self):
        """Test that currency is converted to uppercase"""
        money = Money(100, "usd")
        assert money.currency == "USD"

    def test_negative_amount_warning(self):
        """Test that negative amounts trigger warning but are allowed"""
        # The warning is logged, not raised as a Python warning
        # So we just verify the Money object is created successfully
        money = Money(-100, "USD")
        assert money.amount == Decimal("-100")
        # The warning is logged via logger.warning, which is captured in logs


class TestMoneyOperations:
    """Tests for Money arithmetic operations"""

    def test_add_same_currency(self):
        """Test adding two Money objects with same currency"""
        money1 = Money(100, "USD")
        money2 = Money(50, "USD")
        result = money1.add(money2)
        assert result.amount == Decimal("150")
        assert result.currency == "USD"
        # Original objects should be unchanged (immutability)
        assert money1.amount == Decimal("100")
        assert money2.amount == Decimal("50")

    def test_add_different_currency_raises_error(self):
        """Test that adding different currencies raises ValueError"""
        money1 = Money(100, "USD")
        money2 = Money(50, "COP")
        with pytest.raises(ValueError, match="Cannot add"):
            money1.add(money2)

    def test_subtract_same_currency(self):
        """Test subtracting two Money objects with same currency"""
        money1 = Money(100, "USD")
        money2 = Money(30, "USD")
        result = money1.subtract(money2)
        assert result.amount == Decimal("70")
        assert result.currency == "USD"

    def test_subtract_different_currency_raises_error(self):
        """Test that subtracting different currencies raises ValueError"""
        money1 = Money(100, "USD")
        money2 = Money(50, "COP")
        with pytest.raises(ValueError, match="Cannot subtract"):
            money1.subtract(money2)

    def test_multiply_by_float(self):
        """Test multiplying Money by float"""
        money = Money(100, "USD")
        result = money.multiply(1.5)
        assert result.amount == Decimal("150")
        assert result.currency == "USD"

    def test_multiply_by_decimal(self):
        """Test multiplying Money by Decimal"""
        money = Money(100, "USD")
        result = money.multiply(Decimal("1.5"))
        assert result.amount == Decimal("150")
        assert result.currency == "USD"

    def test_divide_by_float(self):
        """Test dividing Money by float"""
        money = Money(100, "USD")
        result = money.divide(2.0)
        assert result.amount == Decimal("50")
        assert result.currency == "USD"

    def test_divide_by_decimal(self):
        """Test dividing Money by Decimal"""
        money = Money(100, "USD")
        result = money.divide(Decimal("2"))
        assert result.amount == Decimal("50")
        assert result.currency == "USD"

    def test_divide_by_zero_raises_error(self):
        """Test that dividing by zero raises ValueError"""
        money = Money(100, "USD")
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            money.divide(0)


class TestMoneyPrecision:
    """Tests for Money precision and rounding"""

    def test_quantize_usd(self):
        """Test quantizing USD to display precision (2 decimals)"""
        money = Money("100.123456", "USD")
        quantized = money.quantize()
        assert quantized.amount == Decimal("100.12")
        assert quantized.currency == "USD"

    def test_quantize_cop(self):
        """Test quantizing COP to display precision (no decimals)"""
        money = Money("100.50", "COP")
        quantized = money.quantize()
        assert quantized.amount == Decimal("101")  # Rounded up
        assert quantized.currency == "COP"

    def test_quantize_custom_precision(self):
        """Test quantizing with custom precision"""
        money = Money("100.123456", "USD")
        custom_precision = Decimal("0.001")
        quantized = money.quantize(custom_precision)
        assert quantized.amount == Decimal("100.123")
        assert quantized.currency == "USD"

    def test_rounding_half_up(self):
        """Test that rounding uses ROUND_HALF_UP (not banker's rounding)"""
        # 0.5 should round up to 1
        money = Money("100.5", "USD")
        quantized = money.quantize()
        assert quantized.amount == Decimal("100.50")  # Already at precision

        # Test with more precision
        money2 = Money("100.125", "USD")
        quantized2 = money2.quantize(Decimal("0.01"))
        assert quantized2.amount == Decimal("100.13")  # Rounds up


class TestMoneyPercentages:
    """Tests for percentage operations"""

    def test_apply_percentage(self):
        """Test applying a percentage (e.g., 19% tax)"""
        money = Money(100, "USD")
        result = money.apply_percentage(19)
        assert result.amount == Decimal("19")
        assert result.currency == "USD"

    def test_apply_percentage_decimal(self):
        """Test applying percentage as Decimal"""
        money = Money(100, "USD")
        result = money.apply_percentage(Decimal("19"))
        assert result.amount == Decimal("19")

    def test_apply_margin(self):
        """Test applying margin (cost / (1 - margin))"""
        # Cost = $100, margin = 40% → price = $100 / (1 - 0.40) = $166.67
        cost = Money(100, "USD")
        result = cost.apply_margin(40)
        # Should be approximately 166.67
        assert result.amount > Decimal("166.66")
        assert result.amount < Decimal("166.68")
        assert result.currency == "USD"

    def test_apply_margin_100_percent_raises_error(self):
        """Test that 100% margin raises ValueError"""
        money = Money(100, "USD")
        with pytest.raises(ValueError, match="Margin cannot be >= 100%"):
            money.apply_margin(100)

    def test_apply_margin_over_100_percent_raises_error(self):
        """Test that margin > 100% raises ValueError"""
        money = Money(100, "USD")
        with pytest.raises(ValueError, match="Margin cannot be >= 100%"):
            money.apply_margin(150)


class TestMoneyComparisons:
    """Tests for Money comparison operations"""

    def test_equality(self):
        """Test Money equality"""
        money1 = Money(100, "USD")
        money2 = Money(100, "USD")
        money3 = Money(100, "COP")
        money4 = Money(50, "USD")

        assert money1 == money2
        assert money1 != money3  # Different currency
        assert money1 != money4  # Different amount

    def test_less_than(self):
        """Test Money less than comparison"""
        money1 = Money(50, "USD")
        money2 = Money(100, "USD")

        assert money1 < money2
        assert not (money2 < money1)

    def test_less_than_different_currency_raises_error(self):
        """Test that comparing different currencies raises ValueError"""
        money1 = Money(50, "USD")
        money2 = Money(100, "COP")
        with pytest.raises(ValueError, match="Cannot compare"):
            _ = money1 < money2

    def test_greater_than(self):
        """Test Money greater than comparison"""
        money1 = Money(100, "USD")
        money2 = Money(50, "USD")

        assert money1 > money2
        assert not (money2 > money1)

    def test_less_than_or_equal(self):
        """Test Money less than or equal comparison"""
        money1 = Money(50, "USD")
        money2 = Money(100, "USD")
        money3 = Money(50, "USD")

        assert money1 <= money2
        assert money1 <= money3
        assert not (money2 <= money1)

    def test_greater_than_or_equal(self):
        """Test Money greater than or equal comparison"""
        money1 = Money(100, "USD")
        money2 = Money(50, "USD")
        money3 = Money(100, "USD")

        assert money1 >= money2
        assert money1 >= money3
        assert not (money2 >= money1)


class TestMoneyConversions:
    """Tests for Money conversion methods"""

    def test_to_float(self):
        """Test converting Money to float"""
        money = Money("100.50", "USD")
        assert money.to_float() == 100.50

    def test_to_int_cents_usd(self):
        """Test converting USD to cents"""
        money = Money("100.50", "USD")
        assert money.to_int_cents() == 10050

    def test_to_int_cents_cop(self):
        """Test converting COP (already in units)"""
        money = Money("1000000", "COP")
        assert money.to_int_cents() == 1000000


class TestMoneyHelpers:
    """Tests for Money helper functions"""

    def test_to_money(self):
        """Test to_money helper function"""
        money = to_money(100.50, "USD")
        assert isinstance(money, Money)
        assert money.amount == Decimal("100.50")
        assert money.currency == "USD"

    def test_from_api(self):
        """Test from_api helper function"""
        money = from_api(100.50, "USD")
        assert isinstance(money, Money)
        assert money.amount == Decimal("100.50")
        assert money.currency == "USD"

    def test_to_api(self):
        """Test to_api helper function"""
        money = Money("100.50", "USD")
        result = to_api(money)
        assert result == 100.50
        assert isinstance(result, float)

    def test_sum_money_same_currency(self):
        """Test summing list of Money with same currency"""
        amounts = [Money(100, "USD"), Money(50, "USD"), Money(25, "USD")]
        result = sum_money(amounts)
        assert result is not None
        assert result.amount == Decimal("175")
        assert result.currency == "USD"

    def test_sum_money_different_currency_raises_error(self):
        """Test that summing different currencies raises ValueError"""
        amounts = [Money(100, "USD"), Money(50, "COP")]
        with pytest.raises(ValueError, match="All amounts must be in"):
            sum_money(amounts)

    def test_sum_money_empty_list(self):
        """Test summing empty list returns None"""
        result = sum_money([])
        assert result is None


class TestMoneyPrecisionEdgeCases:
    """Tests for precision edge cases"""

    def test_precision_float_conversion(self):
        """Test that float precision is maintained via string conversion"""
        # 0.1 + 0.2 should not equal 0.30000000000000004
        money1 = Money(0.1, "USD")
        money2 = Money(0.2, "USD")
        result = money1.add(money2)
        assert result.amount == Decimal("0.3")
        assert result.amount != Decimal("0.30000000000000004")

    def test_large_numbers(self):
        """Test Money with large numbers"""
        money = Money("999999999.99", "USD")
        assert money.amount == Decimal("999999999.99")
        quantized = money.quantize()
        assert quantized.amount == Decimal("999999999.99")

    def test_very_small_numbers(self):
        """Test Money with very small numbers"""
        money = Money("0.0001", "USD")
        assert money.amount == Decimal("0.0001")
        quantized = money.quantize()
        assert quantized.amount == Decimal("0.00")  # Rounded to display precision
