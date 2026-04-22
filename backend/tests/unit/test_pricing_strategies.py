"""
Unit tests for pricing strategies
"""

from unittest.mock import Mock

import pytest

from app.core.pricing_strategies import (
    FixedPricingStrategy,
    HourlyPricingStrategy,
    PricingStrategy,
    PricingStrategyFactory,
    ProjectValuePricingStrategy,
    RecurringPricingStrategy,
)
from app.models.service import Service


@pytest.mark.unit
class TestHourlyPricingStrategy:
    """Tests for HourlyPricingStrategy"""

    def test_calculate_with_valid_hours(self):
        """Test hourly pricing calculation with valid hours"""
        strategy = HourlyPricingStrategy()
        service = Mock(spec=Service)
        service.default_margin_target = 0.30

        item = {"estimated_hours": 10.0}
        blended_cost_rate = 50.0

        result = strategy.calculate(item, service, blended_cost_rate)

        # Internal cost: 50 * 10 = 500
        # Client price: 500 / (1 - 0.30) = 500 / 0.70 = 714.29
        assert result["internal_cost"] == 500.0
        assert result["client_price"] > 714.0
        assert result["client_price"] < 715.0

    def test_calculate_with_zero_hours(self):
        """Test hourly pricing with zero hours"""
        strategy = HourlyPricingStrategy()
        service = Mock(spec=Service)
        service.default_margin_target = 0.30

        item = {"estimated_hours": 0}
        blended_cost_rate = 50.0

        result = strategy.calculate(item, service, blended_cost_rate)

        assert result["internal_cost"] == 0.0
        assert result["client_price"] == 0.0

    def test_calculate_with_invalid_margin(self):
        """Test hourly pricing with invalid margin (fallback)"""
        strategy = HourlyPricingStrategy()
        service = Mock(spec=Service)
        service.default_margin_target = 1.5  # Invalid margin

        item = {"estimated_hours": 10.0}
        blended_cost_rate = 50.0

        result = strategy.calculate(item, service, blended_cost_rate)

        # Should fallback to internal_cost as client_price
        assert result["internal_cost"] == 500.0
        assert result["client_price"] == 500.0


@pytest.mark.unit
class TestFixedPricingStrategy:
    """Tests for FixedPricingStrategy"""

    def test_calculate_with_fixed_price(self):
        """Test fixed pricing calculation"""
        strategy = FixedPricingStrategy()
        service = Mock(spec=Service)
        service.fixed_price = 1000.0

        item = {"fixed_price": 1000.0, "quantity": 2.0}
        blended_cost_rate = 50.0

        result = strategy.calculate(item, service, blended_cost_rate)

        # Client price: 1000 * 2 = 2000
        # Internal cost (no hours): 2000 * 0.6 = 1200
        assert result["client_price"] == 2000.0
        assert result["internal_cost"] == 1200.0

    def test_calculate_with_estimated_hours(self):
        """Test fixed pricing with estimated hours"""
        strategy = FixedPricingStrategy()
        service = Mock(spec=Service)
        service.fixed_price = 1000.0

        item = {"fixed_price": 1000.0, "quantity": 1.0, "estimated_hours": 15.0}
        blended_cost_rate = 50.0

        result = strategy.calculate(item, service, blended_cost_rate)

        # Client price: 1000 * 1 = 1000
        # Internal cost: 50 * 15 * 1 = 750
        assert result["client_price"] == 1000.0
        assert result["internal_cost"] == 750.0

    def test_calculate_with_invalid_price(self):
        """Test fixed pricing with invalid price"""
        strategy = FixedPricingStrategy()
        service = Mock(spec=Service)
        service.fixed_price = None

        item = {"fixed_price": None}
        blended_cost_rate = 50.0

        result = strategy.calculate(item, service, blended_cost_rate)

        assert result["internal_cost"] == 0.0
        assert result["client_price"] == 0.0


@pytest.mark.unit
class TestRecurringPricingStrategy:
    """Tests for RecurringPricingStrategy"""

    def test_calculate_monthly_recurring(self):
        """Test recurring pricing for monthly billing"""
        strategy = RecurringPricingStrategy()
        service = Mock(spec=Service)
        service.recurring_price = 500.0
        service.billing_frequency = "monthly"

        item = {"recurring_price": 500.0, "quantity": 1.0}
        blended_cost_rate = 50.0

        result = strategy.calculate(item, service, blended_cost_rate)

        # Client price: 500 * 1 = 500
        # Internal cost (estimated): 50 * 32 * 1 = 1600 (32 hours/month estimate)
        assert result["client_price"] == 500.0
        assert result["internal_cost"] == 1600.0

    def test_calculate_annual_recurring(self):
        """Test recurring pricing for annual billing"""
        strategy = RecurringPricingStrategy()
        service = Mock(spec=Service)
        service.recurring_price = 5000.0
        service.billing_frequency = "annual"

        item = {"recurring_price": 5000.0, "quantity": 1.0}
        blended_cost_rate = 50.0

        result = strategy.calculate(item, service, blended_cost_rate)

        # Client price: 5000 * 1 = 5000
        # Internal cost (estimated): 50 * 32 * 12 * 1 = 19200 (annual estimate)
        assert result["client_price"] == 5000.0
        assert result["internal_cost"] == 19200.0

    def test_calculate_with_estimated_hours(self):
        """Test recurring pricing with estimated hours"""
        strategy = RecurringPricingStrategy()
        service = Mock(spec=Service)
        service.recurring_price = 500.0

        item = {"recurring_price": 500.0, "estimated_hours": 20.0}
        blended_cost_rate = 50.0

        result = strategy.calculate(item, service, blended_cost_rate)

        # Client price: 500
        # Internal cost: 50 * 20 = 1000
        assert result["client_price"] == 500.0
        assert result["internal_cost"] == 1000.0


@pytest.mark.unit
class TestProjectValuePricingStrategy:
    """Tests for ProjectValuePricingStrategy"""

    def test_calculate_with_project_value(self):
        """Test project value pricing calculation"""
        strategy = ProjectValuePricingStrategy()
        service = Mock(spec=Service)

        item = {"project_value": 5000.0, "quantity": 1.0}
        blended_cost_rate = 50.0

        result = strategy.calculate(item, service, blended_cost_rate)

        # Client price: 5000 * 1 = 5000
        # Internal cost (no hours): 5000 * 0.5 = 2500
        assert result["client_price"] == 5000.0
        assert result["internal_cost"] == 2500.0

    def test_calculate_with_estimated_hours(self):
        """Test project value pricing with estimated hours"""
        strategy = ProjectValuePricingStrategy()
        service = Mock(spec=Service)

        item = {"project_value": 5000.0, "quantity": 1.0, "estimated_hours": 40.0}
        blended_cost_rate = 50.0

        result = strategy.calculate(item, service, blended_cost_rate)

        # Client price: 5000 * 1 = 5000
        # Internal cost: 50 * 40 * 1 = 2000
        assert result["client_price"] == 5000.0
        assert result["internal_cost"] == 2000.0

    def test_calculate_with_fixed_price_fallback(self):
        """Test project value pricing using fixed_price as fallback"""
        strategy = ProjectValuePricingStrategy()
        service = Mock(spec=Service)

        item = {"fixed_price": 3000.0, "quantity": 1.0}
        blended_cost_rate = 50.0

        result = strategy.calculate(item, service, blended_cost_rate)

        # Should use fixed_price as project_value
        assert result["client_price"] == 3000.0
        assert result["internal_cost"] == 1500.0  # 50% of 3000


@pytest.mark.unit
class TestPricingStrategyFactory:
    """Tests for PricingStrategyFactory"""

    def test_get_hourly_strategy(self):
        """Test getting hourly strategy"""
        strategy = PricingStrategyFactory.get_strategy("hourly")
        assert isinstance(strategy, HourlyPricingStrategy)

    def test_get_fixed_strategy(self):
        """Test getting fixed strategy"""
        strategy = PricingStrategyFactory.get_strategy("fixed")
        assert isinstance(strategy, FixedPricingStrategy)

    def test_get_recurring_strategy(self):
        """Test getting recurring strategy"""
        strategy = PricingStrategyFactory.get_strategy("recurring")
        assert isinstance(strategy, RecurringPricingStrategy)

    def test_get_project_value_strategy(self):
        """Test getting project value strategy"""
        strategy = PricingStrategyFactory.get_strategy("project_value")
        assert isinstance(strategy, ProjectValuePricingStrategy)

    def test_get_unknown_strategy_defaults_to_hourly(self):
        """Test that unknown strategy defaults to hourly"""
        strategy = PricingStrategyFactory.get_strategy("unknown_type")
        assert isinstance(strategy, HourlyPricingStrategy)

    def test_get_strategy_with_none_defaults_to_hourly(self):
        """Test that None strategy defaults to hourly"""
        strategy = PricingStrategyFactory.get_strategy(None)
        assert isinstance(strategy, HourlyPricingStrategy)

    def test_register_custom_strategy(self):
        """Test registering a custom strategy"""

        class CustomStrategy(PricingStrategy):
            def calculate(self, item, service, blended_cost_rate):
                return {"internal_cost": 100.0, "client_price": 200.0}

        custom_strategy = CustomStrategy()
        PricingStrategyFactory.register_strategy("custom", custom_strategy)

        retrieved = PricingStrategyFactory.get_strategy("custom")
        assert isinstance(retrieved, CustomStrategy)

        # Test that it works
        result = retrieved.calculate({}, Mock(), 50.0)
        assert result["internal_cost"] == 100.0
        assert result["client_price"] == 200.0
