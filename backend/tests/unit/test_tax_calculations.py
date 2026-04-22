"""
Unit tests for tax calculations
"""

import uuid

import pytest

from app.core.calculations import calculate_quote_totals_enhanced
from app.models.tax import Tax


@pytest.mark.unit
class TestTaxCalculations:
    """Tests for tax calculation logic"""

    async def test_single_tax_calculation(self, db_session, test_organization, test_service):
        """Test single tax calculation"""
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

        # Client price: ~714.29
        # Tax: 714.29 * 0.19 = 135.72
        # Total with taxes: 714.29 + 135.72 = 850.01
        assert result["total_taxes"] > 135.0
        assert result["total_taxes"] < 136.0
        assert result["total_with_taxes"] > result["total_client_price"]
        assert len(result["taxes"]) == 1
        assert result["taxes"][0]["id"] == tax.id
        assert result["taxes"][0]["percentage"] == 19.0

    async def test_multiple_taxes(self, db_session, test_organization, test_service):
        """Test multiple taxes calculation"""
        test_service.pricing_type = "hourly"
        test_service.default_margin_target = 0.30
        db_session.add(test_service)
        await db_session.commit()

        # Create multiple taxes with unique codes
        unique_code1 = f"IVA_CO_{uuid.uuid4().hex[:8]}"
        unique_code2 = f"TX_AR_{uuid.uuid4().hex[:8]}"
        tax1 = Tax(
            name="IVA",
            code=unique_code1,
            percentage=19.0,
            is_active=True,
            organization_id=test_organization.id,
        )
        tax2 = Tax(
            name="Transaction Cost",
            code=unique_code2,
            percentage=5.0,
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(tax1)
        db_session.add(tax2)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [{"service_id": test_service.id, "estimated_hours": 10.0}]

        result = await calculate_quote_totals_enhanced(
            db_session, items, blended_cost_rate, tax_ids=[tax1.id, tax2.id]
        )

        # Client price: ~714.29
        # Tax 1: 714.29 * 0.19 = 135.72
        # Tax 2: 714.29 * 0.05 = 35.71
        # Total taxes: 171.43
        assert result["total_taxes"] > 171.0
        assert result["total_taxes"] < 172.0
        assert len(result["taxes"]) == 2
        # Allow small rounding differences
        assert (
            abs(result["total_with_taxes"] - (result["total_client_price"] + result["total_taxes"]))
            < 0.01
        )

    async def test_tax_on_expenses(self, db_session, test_organization, test_service):
        """Test that taxes are calculated on total price including expenses"""
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
        expenses = [{"name": "Expense", "cost": 200.0, "markup_percentage": 0.20, "quantity": 1.0}]

        result = await calculate_quote_totals_enhanced(
            db_session, items, blended_cost_rate, tax_ids=[tax.id], expenses=expenses
        )

        # Total client price: ~714 (service) + 240 (expense) = ~954
        # Tax: 954 * 0.19 = 181.26
        assert result["total_taxes"] > 180.0
        assert result["total_taxes"] < 182.0
        assert result["total_with_taxes"] > result["total_client_price"]

    async def test_tax_on_revisions(self, db_session, test_organization, test_service):
        """Test that taxes are calculated including revision costs"""
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
            db_session,
            items,
            blended_cost_rate,
            tax_ids=[tax.id],
            revisions_included=2,
            revision_cost_per_additional=100.0,
            revisions_count=5,  # 3 additional revisions = 300
        )

        # Client price: ~714 (service) + 300 (revisions) = ~1014
        # Tax: 1014 * 0.19 = 192.66
        assert result["revisions_cost"] == 300.0
        assert result["total_taxes"] > 192.0
        assert result["total_taxes"] < 193.0

    async def test_inactive_tax_excluded(self, db_session, test_organization, test_service):
        """Test that inactive taxes are excluded"""
        test_service.pricing_type = "hourly"
        db_session.add(test_service)
        await db_session.commit()

        # Create active and inactive taxes with unique codes
        unique_code1 = f"ACTIVE_{uuid.uuid4().hex[:8]}"
        unique_code2 = f"INACTIVE_{uuid.uuid4().hex[:8]}"
        active_tax = Tax(
            name="Active Tax",
            code=unique_code1,
            percentage=10.0,
            is_active=True,
            organization_id=test_organization.id,
        )
        inactive_tax = Tax(
            name="Inactive Tax",
            code=unique_code2,
            percentage=20.0,
            is_active=False,  # Inactive
            organization_id=test_organization.id,
        )
        db_session.add(active_tax)
        db_session.add(inactive_tax)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [{"service_id": test_service.id, "estimated_hours": 10.0}]

        result = await calculate_quote_totals_enhanced(
            db_session, items, blended_cost_rate, tax_ids=[active_tax.id, inactive_tax.id]
        )

        # Only active tax should be applied
        assert len(result["taxes"]) == 1
        assert result["taxes"][0]["id"] == active_tax.id
        assert result["taxes"][0]["percentage"] == 10.0

    async def test_tax_breakdown(self, db_session, test_organization, test_service):
        """Test tax breakdown in response"""
        test_service.pricing_type = "hourly"
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

        # Check tax breakdown structure
        assert "taxes" in result
        assert len(result["taxes"]) == 1
        tax_breakdown = result["taxes"][0]
        assert "id" in tax_breakdown
        assert "name" in tax_breakdown
        assert "code" in tax_breakdown
        assert "percentage" in tax_breakdown
        assert "amount" in tax_breakdown
        assert tax_breakdown["name"] == "IVA"
        assert tax_breakdown["code"].startswith("IVA_CO")  # Code is unique, so check prefix
        assert tax_breakdown["percentage"] == 19.0
        assert tax_breakdown["amount"] > 0

    async def test_zero_tax(self, db_session, test_organization, test_service):
        """Test zero percentage tax"""
        test_service.pricing_type = "hourly"
        db_session.add(test_service)
        await db_session.commit()

        # Create tax with 0% and unique code
        unique_code = f"ZERO_{uuid.uuid4().hex[:8]}"
        tax = Tax(
            name="Zero Tax",
            code=unique_code,
            percentage=0.0,
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

        # Tax should be zero
        assert result["total_taxes"] == 0.0
        assert result["total_with_taxes"] == result["total_client_price"]

    async def test_high_tax_percentage(self, db_session, test_organization, test_service):
        """Test high tax percentage (e.g., 50%)"""
        test_service.pricing_type = "hourly"
        db_session.add(test_service)
        await db_session.commit()

        # Create high tax with unique code
        unique_code = f"HIGH_{uuid.uuid4().hex[:8]}"
        tax = Tax(
            name="High Tax",
            code=unique_code,
            percentage=50.0,
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

        # Client price: ~714.29
        # Tax: 714.29 * 0.50 = 357.15
        # Total: 1071.44
        assert result["total_taxes"] > 357.0
        assert result["total_taxes"] < 358.0
        assert result["total_with_taxes"] > 1070.0

    async def test_no_taxes(self, db_session, test_organization, test_service):
        """Test calculation without taxes"""
        test_service.pricing_type = "hourly"
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [{"service_id": test_service.id, "estimated_hours": 10.0}]

        result = await calculate_quote_totals_enhanced(
            db_session, items, blended_cost_rate, tax_ids=None
        )

        # Should have no taxes
        assert result["total_taxes"] == 0.0
        assert result["total_with_taxes"] == result["total_client_price"]
        assert len(result["taxes"]) == 0

    async def test_tax_on_zero_price(self, db_session, test_organization):
        """Test tax calculation on zero price (edge case)"""
        blended_cost_rate = 50.0
        items = []  # No items

        result = await calculate_quote_totals_enhanced(
            db_session, items, blended_cost_rate, tax_ids=[]
        )

        # Should handle zero price gracefully
        assert result["total_taxes"] == 0.0
        assert result["total_with_taxes"] == 0.0
