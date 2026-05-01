"""
Unit tests for calculation functions
"""

import uuid
from decimal import Decimal

import pytest

from app.core.calculations import calculate_blended_cost_rate, calculate_quote_totals_enhanced
from app.models.cost import CostFixed
from app.models.settings import AgencySettings
from app.models.tax import Tax
from app.models.team import TeamMember


@pytest.mark.unit
class TestBlendedCostRate:
    """Tests for blended cost rate calculation"""

    async def test_blended_cost_rate_single_member(self, db_session, test_organization):
        """Test blended cost rate with single team member"""
        # Create settings
        settings = AgencySettings(primary_currency="USD", currency_symbol="$")
        db_session.add(settings)
        await db_session.commit()

        # Create team member with organization_id
        member = TeamMember(
            name="Test Member",
            role="Developer",
            salary_monthly_brute=5000.00,
            billable_hours_per_week=32,
            currency="USD",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(member)
        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(member)

        # Verify member was saved correctly
        from sqlalchemy import select

        check_result = await db_session.execute(
            select(TeamMember).where(
                TeamMember.id == member.id, TeamMember.organization_id == test_organization.id
            )
        )
        saved_member = check_result.scalar_one_or_none()
        assert saved_member is not None, "TeamMember should be saved"
        assert saved_member.billable_hours_per_week == 32

        # Verify the query that calculate_blended_cost_rate uses finds the member
        query_check = select(TeamMember).where(TeamMember.is_active)
        query_check = query_check.where(TeamMember.organization_id == test_organization.id)
        result_check = await db_session.execute(query_check)
        found_members = result_check.scalars().all()
        assert len(found_members) > 0, (
            f"Query should find TeamMember, found {len(found_members)} members"
        )

        result = await calculate_blended_cost_rate(
            db_session, "USD", use_cache=False, tenant_id=test_organization.id
        )

        # Expected: 5000 / (32 * 4.33) = 5000 / 138.56 = 36.08
        assert result > 0, (
            f"BCR should be > 0, got {result}. Found {len(found_members)} members in query check"
        )
        assert isinstance(result, Decimal)
        assert abs(float(result) - 36.08) < 1.0  # Allow small rounding differences

    async def test_blended_cost_rate_with_fixed_costs(self, db_session, test_organization):
        """Test blended cost rate including fixed costs"""
        # Create settings
        settings = AgencySettings(primary_currency="USD", currency_symbol="$")
        db_session.add(settings)
        await db_session.commit()

        # Create team member with organization_id
        member = TeamMember(
            name="Test Member",
            role="Developer",
            salary_monthly_brute=5000.00,
            billable_hours_per_week=32,
            currency="USD",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(member)

        # Create fixed cost with organization_id
        cost = CostFixed(
            name="Test Cost",
            amount_monthly=2000.00,
            currency="USD",
            category="overhead",
            organization_id=test_organization.id,
        )
        db_session.add(cost)
        await db_session.commit()

        result = await calculate_blended_cost_rate(
            db_session, "USD", use_cache=False, tenant_id=test_organization.id
        )

        # Expected: (5000 + 2000) / (32 * 4.33) = 7000 / 138.56 = 50.52
        assert result > 0
        assert isinstance(result, Decimal)
        # Should be higher than without fixed costs
        assert result > 36.0

    async def test_blended_cost_rate_zero_hours(self, db_session):
        """Test blended cost rate with zero billable hours"""
        from sqlalchemy import delete

        # Clean up any existing data first
        await db_session.execute(delete(CostFixed))
        await db_session.execute(delete(TeamMember))
        await db_session.commit()

        # Create settings
        settings = AgencySettings(primary_currency="USD", currency_symbol="$")
        db_session.add(settings)
        await db_session.commit()

        # Create team member with zero hours (no fixed costs)
        member = TeamMember(
            name="Test Member Zero Hours",
            role="Developer",
            salary_monthly_brute=5000.00,
            billable_hours_per_week=0,
            currency="USD",
            is_active=True,
        )
        db_session.add(member)
        await db_session.commit()

        result = await calculate_blended_cost_rate(db_session, "USD", use_cache=False)

        # When hours_per_month is 0, the function should return 0.0
        assert result == 0.0

    async def test_blended_cost_rate_multiple_currencies(self, db_session, test_organization):
        """Test blended cost rate with multiple currencies"""
        # Create settings
        settings = AgencySettings(primary_currency="USD", currency_symbol="$")
        db_session.add(settings)
        await db_session.commit()

        # Create team members in different currencies
        member_usd = TeamMember(
            name="USD Member",
            role="Developer",
            salary_monthly_brute=5000.00,
            billable_hours_per_week=40,
            currency="USD",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(member_usd)

        # EUR member (assuming 1 EUR = 1.1 USD for simplicity in tests)
        # In real scenario, currency conversion would be handled by normalize_to_primary_currency
        member_eur = TeamMember(
            name="EUR Member",
            role="Designer",
            salary_monthly_brute=4000.00,
            billable_hours_per_week=40,
            currency="EUR",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(member_eur)
        await db_session.commit()

        result = await calculate_blended_cost_rate(
            db_session, "USD", use_cache=False, tenant_id=test_organization.id
        )

        # Should calculate correctly with currency conversion
        assert result > 0
        assert isinstance(result, Decimal)

    async def test_blended_cost_rate_with_social_charges(self, db_session, test_organization):
        """Test blended cost rate with social charges (Sprint 18)"""
        # Create settings
        settings = AgencySettings(primary_currency="USD", currency_symbol="$")
        db_session.add(settings)
        await db_session.commit()

        # Update organization with social charges config
        test_organization.settings = {
            "social_charges_config": {
                "enable_social_charges": True,
                "total_percentage": 50.0,  # 50% social charges
            }
        }
        db_session.add(test_organization)
        await db_session.commit()

        # Create team member
        member = TeamMember(
            name="Test Member",
            role="Developer",
            salary_monthly_brute=5000.00,
            billable_hours_per_week=40,
            currency="USD",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(member)
        await db_session.commit()

        result_with_charges = await calculate_blended_cost_rate(
            db_session, "USD", use_cache=False, tenant_id=test_organization.id
        )

        # Without social charges: 5000 / (40 * 4.33) = 5000 / 173.2 = 28.87
        # With 50% social charges: (5000 * 1.5) / 173.2 = 7500 / 173.2 = 43.30
        assert result_with_charges > 0
        assert isinstance(result_with_charges, Decimal)
        # Should be higher than without social charges
        assert result_with_charges > 28.0

    async def test_blended_cost_rate_cache(self, db_session, test_organization):
        """Test blended cost rate caching"""
        # Create settings
        settings = AgencySettings(primary_currency="USD", currency_symbol="$")
        db_session.add(settings)
        await db_session.commit()

        # Create team member with organization_id
        member = TeamMember(
            name="Test Member",
            role="Developer",
            salary_monthly_brute=5000.00,
            billable_hours_per_week=40,
            currency="USD",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(member)
        await db_session.commit()

        # First call (should calculate)
        result1 = await calculate_blended_cost_rate(
            db_session, "USD", use_cache=True, tenant_id=test_organization.id
        )

        # Second call (should use cache)
        result2 = await calculate_blended_cost_rate(
            db_session, "USD", use_cache=True, tenant_id=test_organization.id
        )

        # Cache round-trip may widen Decimal precision; values must be materially equal
        assert result1 > 0
        assert abs(Decimal(str(result1)) - Decimal(str(result2))) < Decimal("1e-9")

    async def test_blended_cost_rate_zero_costs(self, db_session):
        """Test blended cost rate with zero costs"""
        from sqlalchemy import delete

        # Clean up any existing data
        await db_session.execute(delete(CostFixed))
        await db_session.execute(delete(TeamMember))
        await db_session.commit()

        # Create settings
        settings = AgencySettings(primary_currency="USD", currency_symbol="$")
        db_session.add(settings)
        await db_session.commit()

        # No team members, no fixed costs
        result = await calculate_blended_cost_rate(db_session, "USD", use_cache=False)

        # Should return 0.0 when there are no costs
        assert result == 0.0

    async def test_blended_cost_rate_non_billable_hours(self, db_session, test_organization):
        """Test blended cost rate with non-billable hours percentage"""
        # Create settings
        settings = AgencySettings(primary_currency="USD", currency_symbol="$")
        db_session.add(settings)
        await db_session.commit()

        # Create team member with 20% non-billable hours
        member = TeamMember(
            name="Test Member",
            role="Developer",
            salary_monthly_brute=5000.00,
            billable_hours_per_week=40,
            non_billable_hours_percentage=0.20,  # 20% non-billable
            currency="USD",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(member)
        await db_session.commit()

        result = await calculate_blended_cost_rate(
            db_session, "USD", use_cache=False, tenant_id=test_organization.id
        )

        # Expected: 5000 / (40 * 4.33 * 0.8) = 5000 / 138.56 = 36.08
        assert result > 0
        assert isinstance(result, Decimal)
        # Should be higher than without non-billable hours adjustment
        assert result > 28.0


@pytest.mark.unit
class TestQuoteTotalsEnhanced:
    """Tests for enhanced quote totals calculation (Sprint 15-16)"""

    async def test_hourly_pricing(self, db_session, test_organization, test_service):
        """Test hourly pricing calculation"""
        # Set up service with hourly pricing
        test_service.pricing_type = "hourly"
        test_service.default_margin_target = 0.30  # 30% margin
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 50.0  # $50/hour
        items = [{"service_id": test_service.id, "estimated_hours": 10.0}]

        result = await calculate_quote_totals_enhanced(db_session, items, blended_cost_rate)

        # Internal cost: 50 * 10 = 500
        # Client price: 500 / (1 - 0.30) = 500 / 0.70 = 714.29
        assert result["total_internal_cost"] == 500.0
        assert abs(result["total_client_price"] - 714.29) < 1.0
        assert result["margin_percentage"] > 0.29  # ~30% margin
        assert len(result["items"]) == 1

    async def test_fixed_pricing(self, db_session, test_organization, test_service):
        """Test fixed pricing calculation"""
        # Set up service with fixed pricing
        test_service.pricing_type = "fixed"
        test_service.fixed_price = 1000.0
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [{"service_id": test_service.id, "fixed_price": 1000.0, "quantity": 2.0}]

        result = await calculate_quote_totals_enhanced(db_session, items, blended_cost_rate)

        # Client price: 1000 * 2 = 2000
        # Internal cost: 2000 * 0.6 = 1200 (default 60% if no hours)
        assert result["total_client_price"] == 2000.0
        assert result["total_internal_cost"] == 1200.0
        assert len(result["items"]) == 1

    async def test_fixed_pricing_with_hours(self, db_session, test_organization, test_service):
        """Test fixed pricing with estimated hours"""
        test_service.pricing_type = "fixed"
        test_service.fixed_price = 1000.0
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [
            {
                "service_id": test_service.id,
                "fixed_price": 1000.0,
                "quantity": 1.0,
                "estimated_hours": 15.0,
            }
        ]

        result = await calculate_quote_totals_enhanced(db_session, items, blended_cost_rate)

        # Client price: 1000 * 1 = 1000
        # Internal cost: 50 * 15 * 1 = 750
        assert result["total_client_price"] == 1000.0
        assert result["total_internal_cost"] == 750.0

    async def test_recurring_pricing(self, db_session, test_organization, test_service):
        """Test recurring pricing calculation"""
        test_service.pricing_type = "recurring"
        test_service.recurring_price = 500.0
        test_service.billing_frequency = "monthly"
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [
            {
                "service_id": test_service.id,
                "recurring_price": 500.0,
                "billing_frequency": "monthly",
                "quantity": 1.0,
            }
        ]

        result = await calculate_quote_totals_enhanced(db_session, items, blended_cost_rate)

        # Client price: 500 * 1 = 500
        # Internal cost: 50 * 32 * 1 = 1600 (estimated 32 hours/month)
        assert result["total_client_price"] == 500.0
        assert result["total_internal_cost"] == 1600.0

    async def test_project_value_pricing(self, db_session, test_organization, test_service):
        """Test project value pricing calculation"""
        test_service.pricing_type = "project_value"
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [{"service_id": test_service.id, "project_value": 5000.0, "quantity": 1.0}]

        result = await calculate_quote_totals_enhanced(db_session, items, blended_cost_rate)

        # Client price: 5000 * 1 = 5000
        # Internal cost: 5000 * 0.5 = 2500 (default 50% if no hours)
        assert result["total_client_price"] == 5000.0
        assert result["total_internal_cost"] == 2500.0

    async def test_expenses_with_markup(self, db_session, test_organization, test_service):
        """Test expenses with markup calculation"""
        test_service.pricing_type = "hourly"
        test_service.default_margin_target = 0.30
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [{"service_id": test_service.id, "estimated_hours": 10.0}]
        expenses = [
            {
                "name": "Third-party service",
                "cost": 200.0,
                "markup_percentage": 0.20,  # 20% markup
                "quantity": 1.0,
            }
        ]

        result = await calculate_quote_totals_enhanced(
            db_session, items, blended_cost_rate, expenses=expenses
        )

        # Service: 500 cost, ~714 client price
        # Expense: 200 cost, 240 client price (200 * 1.2)
        assert result["total_expenses_cost"] == 200.0
        assert result["total_expenses_client_price"] == 240.0
        assert result["total_internal_cost"] > 500.0  # Service + expense cost
        assert result["total_client_price"] > 714.0  # Service + expense price
        assert len(result["expenses"]) == 1

    async def test_revisions_calculation(self, db_session, test_organization, test_service):
        """Test revisions cost calculation (Sprint 16)"""
        test_service.pricing_type = "hourly"
        test_service.default_margin_target = 0.30
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [{"service_id": test_service.id, "estimated_hours": 10.0}]

        result = await calculate_quote_totals_enhanced(
            db_session,
            items,
            blended_cost_rate,
            revisions_included=2,
            revision_cost_per_additional=100.0,
            revisions_count=5,  # 3 additional revisions
        )

        # Revisions cost: (5 - 2) * 100 = 300
        assert result["revisions_cost"] == 300.0
        assert result["revisions_included"] == 2
        assert result["revisions_count"] == 5
        assert result["total_client_price"] > 714.0  # Service + revisions

    async def test_revisions_no_additional(self, db_session, test_organization, test_service):
        """Test revisions when count is within included"""
        test_service.pricing_type = "hourly"
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [{"service_id": test_service.id, "estimated_hours": 10.0}]

        result = await calculate_quote_totals_enhanced(
            db_session,
            items,
            blended_cost_rate,
            revisions_included=2,
            revision_cost_per_additional=100.0,
            revisions_count=2,  # Exactly included
        )

        # No additional revisions
        assert result["revisions_cost"] == 0.0

    async def test_taxes_calculation(self, db_session, test_organization, test_service):
        """Test taxes calculation"""
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
        assert result["total_taxes"] > 0
        assert result["total_with_taxes"] > result["total_client_price"]
        assert len(result["taxes"]) == 1
        assert result["taxes"][0]["percentage"] == 19.0

    async def test_multiple_taxes(self, db_session, test_organization, test_service):
        """Test multiple taxes calculation"""
        test_service.pricing_type = "hourly"
        test_service.default_margin_target = 0.30
        db_session.add(test_service)
        await db_session.commit()

        # Create multiple taxes with unique codes
        import uuid

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

        # Total taxes should be sum of both
        assert result["total_taxes"] > 0
        assert len(result["taxes"]) == 2
        assert result["total_with_taxes"] > result["total_client_price"]

    async def test_combined_features(self, db_session, test_organization, test_service):
        """Test combined features: services + expenses + revisions + taxes"""
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
        expenses = [
            {"name": "Third-party", "cost": 200.0, "markup_percentage": 0.20, "quantity": 1.0}
        ]

        result = await calculate_quote_totals_enhanced(
            db_session,
            items,
            blended_cost_rate,
            tax_ids=[tax.id],
            expenses=expenses,
            revisions_included=2,
            revision_cost_per_additional=100.0,
            revisions_count=4,
        )

        # Should have all components
        assert result["total_internal_cost"] > 0
        assert result["total_client_price"] > 0
        assert result["total_expenses_cost"] > 0
        assert result["total_expenses_client_price"] > 0
        assert result["revisions_cost"] > 0
        assert result["total_taxes"] > 0
        assert result["total_with_taxes"] > result["total_client_price"]
        assert result["margin_percentage"] > 0

    async def test_edge_case_zero_hours(self, db_session, test_organization, test_service):
        """Test edge case: zero hours"""
        test_service.pricing_type = "hourly"
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [{"service_id": test_service.id, "estimated_hours": 0.0}]

        result = await calculate_quote_totals_enhanced(db_session, items, blended_cost_rate)

        # Should skip items with zero hours
        assert result["total_internal_cost"] == 0.0
        assert result["total_client_price"] == 0.0
        assert len(result["items"]) == 0

    async def test_edge_case_negative_margin(self, db_session, test_organization, test_service):
        """Test edge case: negative margin (cost > price)"""
        test_service.pricing_type = "fixed"
        test_service.fixed_price = 1000.0
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 200.0  # High cost rate
        items = [
            {
                "service_id": test_service.id,
                "fixed_price": 1000.0,
                "quantity": 1.0,
                "estimated_hours": 10.0,  # Cost: 200 * 10 = 2000 > 1000
            }
        ]

        result = await calculate_quote_totals_enhanced(db_session, items, blended_cost_rate)

        # Should handle negative margin gracefully
        assert result["total_internal_cost"] == 2000.0
        assert result["total_client_price"] == 1000.0
        assert result["margin_percentage"] < 0  # Negative margin

    async def test_edge_case_invalid_service(self, db_session, test_organization):
        """Test edge case: invalid service ID"""
        blended_cost_rate = 50.0
        items = [
            {
                "service_id": 99999,  # Non-existent service
                "estimated_hours": 10.0,
            }
        ]

        result = await calculate_quote_totals_enhanced(db_session, items, blended_cost_rate)

        # Should skip invalid services
        assert result["total_internal_cost"] == 0.0
        assert result["total_client_price"] == 0.0
        assert len(result["items"]) == 0

    async def test_edge_case_empty_items(self, db_session):
        """Test edge case: empty items list"""
        blended_cost_rate = 50.0

        result = await calculate_quote_totals_enhanced(db_session, [], blended_cost_rate)

        # Should return zeros
        assert result["total_internal_cost"] == 0.0
        assert result["total_client_price"] == 0.0
        assert result["margin_percentage"] == 0.0
        assert len(result["items"]) == 0

    async def test_edge_case_invalid_margin(self, db_session, test_organization, test_service):
        """Test edge case: invalid margin target"""
        test_service.pricing_type = "hourly"
        test_service.default_margin_target = 1.5  # Invalid (> 1)
        db_session.add(test_service)
        await db_session.commit()

        blended_cost_rate = 50.0
        items = [{"service_id": test_service.id, "estimated_hours": 10.0}]

        result = await calculate_quote_totals_enhanced(db_session, items, blended_cost_rate)

        # Should fallback to cost = price when margin is invalid
        assert result["total_internal_cost"] == 500.0
        assert result["total_client_price"] == 500.0  # Fallback
        assert result["margin_percentage"] == 0.0
