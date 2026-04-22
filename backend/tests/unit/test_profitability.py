"""
Unit tests for profitability calculations
"""

import uuid

import pytest

from app.core.calculations import calculate_quote_totals_enhanced
from app.models.tax import Tax


@pytest.mark.unit
class TestProfitabilityCalculations:
    """Tests for profitability and margin calculations"""

    async def test_margin_calculation_basic(self, db_session, test_organization, test_service):
        """Test basic margin calculation"""
        test_service.pricing_type = "hourly"
        test_service.default_margin_target = 0.30  # 30% margin
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [{"service_id": test_service.id, "estimated_hours": 10.0}]

        result = await calculate_quote_totals_enhanced(db_session, items, blended_cost_rate)

        # Internal cost: 50 * 10 = 500
        # Client price: 500 / (1 - 0.30) = 714.29
        # Margin: (714.29 - 500) / 714.29 = 0.30 (30%)
        assert result["margin_percentage"] > 0.29
        assert result["margin_percentage"] < 0.31
        assert result["total_client_price"] > result["total_internal_cost"]

    async def test_margin_calculation_high_margin(
        self, db_session, test_organization, test_service
    ):
        """Test high margin calculation (50%)"""
        test_service.pricing_type = "hourly"
        test_service.default_margin_target = 0.50  # 50% margin
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [{"service_id": test_service.id, "estimated_hours": 10.0}]

        result = await calculate_quote_totals_enhanced(db_session, items, blended_cost_rate)

        # Internal cost: 500
        # Client price: 500 / (1 - 0.50) = 1000
        # Margin: (1000 - 500) / 1000 = 0.50 (50%)
        assert result["margin_percentage"] > 0.49
        assert result["margin_percentage"] < 0.51
        assert result["total_client_price"] == 1000.0

    async def test_margin_calculation_low_margin(self, db_session, test_organization, test_service):
        """Test low margin calculation (10%)"""
        test_service.pricing_type = "hourly"
        test_service.default_margin_target = 0.10  # 10% margin
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [{"service_id": test_service.id, "estimated_hours": 10.0}]

        result = await calculate_quote_totals_enhanced(db_session, items, blended_cost_rate)

        # Internal cost: 500
        # Client price: 500 / (1 - 0.10) = 555.56
        # Margin: (555.56 - 500) / 555.56 = 0.10 (10%)
        assert result["margin_percentage"] > 0.09
        assert result["margin_percentage"] < 0.11

    async def test_negative_margin(self, db_session, test_organization, test_service):
        """Test negative margin scenario (cost > price)"""
        test_service.pricing_type = "fixed"
        test_service.fixed_price = 1000.0
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 150.0  # High cost rate
        items = [
            {
                "service_id": test_service.id,
                "fixed_price": 1000.0,
                "quantity": 1.0,
                "estimated_hours": 10.0,  # Cost: 150 * 10 = 1500 > 1000
            }
        ]

        result = await calculate_quote_totals_enhanced(db_session, items, blended_cost_rate)

        # Should handle negative margin
        assert result["margin_percentage"] < 0
        assert result["total_internal_cost"] > result["total_client_price"]

    async def test_zero_margin(self, db_session, test_organization, test_service):
        """Test zero margin scenario (cost = price)"""
        test_service.pricing_type = "fixed"
        test_service.fixed_price = 1000.0
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 100.0
        items = [
            {
                "service_id": test_service.id,
                "fixed_price": 1000.0,
                "quantity": 1.0,
                "estimated_hours": 10.0,  # Cost: 100 * 10 = 1000 = price
            }
        ]

        result = await calculate_quote_totals_enhanced(db_session, items, blended_cost_rate)

        # Margin should be approximately zero
        assert abs(result["margin_percentage"]) < 0.01
        assert result["total_internal_cost"] == result["total_client_price"]

    async def test_margin_with_expenses(self, db_session, test_organization, test_service):
        """Test margin calculation including expenses"""
        test_service.pricing_type = "hourly"
        test_service.default_margin_target = 0.30
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [{"service_id": test_service.id, "estimated_hours": 10.0}]
        expenses = [{"name": "Expense", "cost": 200.0, "markup_percentage": 0.20, "quantity": 1.0}]

        result = await calculate_quote_totals_enhanced(
            db_session, items, blended_cost_rate, expenses=expenses
        )

        # Total cost: 500 (service) + 200 (expense) = 700
        # Total price: ~714 (service) + 240 (expense) = ~954
        # Margin: (954 - 700) / 954 = ~0.27
        assert result["margin_percentage"] > 0
        assert result["total_internal_cost"] == 700.0
        assert result["total_client_price"] > 950.0

    async def test_margin_with_taxes(self, db_session, test_organization, test_service):
        """Test margin calculation (taxes don't affect margin)"""

        test_service.pricing_type = "hourly"
        test_service.default_margin_target = 0.30
        db_session.add(test_service)
        await db_session.commit()

        # Create tax with unique code
        unique_code = f"IVA_CO_{uuid.uuid4().hex[:8]}"
        tax = Tax(
            name="IVA",
            code=unique_code,
            percentage=19.0,
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(tax)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [{"service_id": test_service.id, "estimated_hours": 10.0}]

        result = await calculate_quote_totals_enhanced(
            db_session, items, blended_cost_rate, tax_ids=[tax.id]
        )

        # Margin should be calculated on price before taxes
        # Internal cost: 500
        # Client price: ~714.29
        # Margin: (714.29 - 500) / 714.29 = 0.30
        # Taxes are added after margin calculation
        assert result["margin_percentage"] > 0.29
        assert result["margin_percentage"] < 0.31
        assert result["total_with_taxes"] > result["total_client_price"]

    async def test_profit_per_item(self, db_session, test_organization, test_service):
        """Test profit calculation per item"""
        test_service.pricing_type = "hourly"
        test_service.default_margin_target = 0.30
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [{"service_id": test_service.id, "estimated_hours": 10.0}]

        result = await calculate_quote_totals_enhanced(db_session, items, blended_cost_rate)

        # Check item breakdown
        assert len(result["items"]) == 1
        item = result["items"][0]
        assert item["internal_cost"] == 500.0
        assert item["client_price"] > 714.0
        assert item["margin"] > 29.0  # Percentage
        assert item["margin"] < 31.0

    async def test_multiple_items_margin(self, db_session, test_organization):
        """Test margin calculation with multiple items"""
        from app.models.service import Service

        # Create multiple services
        service1 = Service(
            name="Service 1",
            pricing_type="hourly",
            default_margin_target=0.30,
            is_active=True,
            organization_id=test_organization.id,
        )
        service2 = Service(
            name="Service 2",
            pricing_type="hourly",
            default_margin_target=0.40,
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(service1)
        db_session.add(service2)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [
            {"service_id": service1.id, "estimated_hours": 10.0},
            {"service_id": service2.id, "estimated_hours": 5.0},
        ]

        result = await calculate_quote_totals_enhanced(db_session, items, blended_cost_rate)

        # Service 1: 500 cost, ~714 price
        # Service 2: 250 cost, ~417 price (40% margin)
        # Total: 750 cost, ~1131 price
        # Overall margin: (1131 - 750) / 1131 = ~0.34
        assert result["total_internal_cost"] == 750.0
        assert result["total_client_price"] > 1130.0
        assert result["margin_percentage"] > 0.30
        assert len(result["items"]) == 2
