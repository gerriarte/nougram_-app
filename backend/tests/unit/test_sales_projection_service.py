"""
Unit tests for sales projection service
"""

import pytest

from app.models.service import Service
from app.services.sales_projection_service import calculate_sales_projection


@pytest.mark.unit
class TestSalesProjectionService:
    """Tests for sales projection service"""

    async def test_calculate_sales_projection_basic(
        self, db_session, test_organization, test_service
    ):
        """Test basic sales projection calculation"""
        test_service.default_margin_target = 0.30
        db_session.add(test_service)
        await db_session.commit()

        # Create team member for BCR calculation
        from app.models.team import TeamMember

        member = TeamMember(
            name="Test Member",
            role="Developer",
            salary_monthly_brute=5000.0,
            billable_hours_per_week=40,
            currency="USD",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(member)
        await db_session.commit()

        result = await calculate_sales_projection(
            db_session,
            test_organization.id,
            [test_service.id],
            {test_service.id: 100.0},  # 100 hours
            win_rate=0.85,
            scenario="realistic",
            period_months=12,
            currency="USD",
        )

        assert result["scenario"] == "realistic"
        assert result["period_months"] == 12
        # Effective win rate: 0.85 * 0.85 = 0.7225 for realistic scenario
        assert result["win_rate"] > 0.7
        assert result["win_rate"] < 0.75
        assert result["currency"] == "USD"
        assert result["bcr"] > 0
        assert len(result["service_projections"]) == 1
        assert len(result["monthly_projections"]) == 12
        assert "summary" in result
        assert result["summary"]["total_revenue"] > 0
        assert result["summary"]["total_costs"] > 0
        assert result["summary"]["total_profit"] > 0

    async def test_calculate_sales_projection_conservative(
        self, db_session, test_organization, test_service
    ):
        """Test conservative scenario"""
        test_service.default_margin_target = 0.30
        db_session.add(test_service)
        await db_session.commit()

        from app.models.team import TeamMember

        member = TeamMember(
            name="Test Member",
            role="Developer",
            salary_monthly_brute=5000.0,
            billable_hours_per_week=40,
            currency="USD",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(member)
        await db_session.commit()

        result = await calculate_sales_projection(
            db_session,
            test_organization.id,
            [test_service.id],
            {test_service.id: 100.0},
            win_rate=0.85,
            scenario="conservative",
            period_months=12,
            currency="USD",
        )

        # Conservative should have lower win rate
        assert result["scenario"] == "conservative"
        assert result["win_rate"] < 0.85  # Reduced by scenario multiplier

    async def test_calculate_sales_projection_optimistic(
        self, db_session, test_organization, test_service
    ):
        """Test optimistic scenario"""
        test_service.default_margin_target = 0.30
        db_session.add(test_service)
        await db_session.commit()

        from app.models.team import TeamMember

        member = TeamMember(
            name="Test Member",
            role="Developer",
            salary_monthly_brute=5000.0,
            billable_hours_per_week=40,
            currency="USD",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(member)
        await db_session.commit()

        result = await calculate_sales_projection(
            db_session,
            test_organization.id,
            [test_service.id],
            {test_service.id: 100.0},
            win_rate=0.85,
            scenario="optimistic",
            period_months=12,
            currency="USD",
        )

        # Optimistic should have higher win rate
        assert result["scenario"] == "optimistic"
        assert result["win_rate"] == 0.85  # Full win rate

    async def test_calculate_sales_projection_no_services(self, db_session, test_organization):
        """Test projection with no valid services"""
        with pytest.raises(ValueError, match="No valid services found"):
            await calculate_sales_projection(
                db_session,
                test_organization.id,
                [99999],  # Non-existent service
                {99999: 100.0},
                win_rate=0.85,
                scenario="realistic",
                period_months=12,
                currency="USD",
            )

    async def test_calculate_sales_projection_multiple_services(
        self, db_session, test_organization
    ):
        """Test projection with multiple services"""
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

        from app.models.team import TeamMember

        member = TeamMember(
            name="Test Member",
            role="Developer",
            salary_monthly_brute=5000.0,
            billable_hours_per_week=40,
            currency="USD",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(member)
        await db_session.commit()

        result = await calculate_sales_projection(
            db_session,
            test_organization.id,
            [service1.id, service2.id],
            {service1.id: 50.0, service2.id: 75.0},
            win_rate=0.85,
            scenario="realistic",
            period_months=12,
            currency="USD",
        )

        assert len(result["service_projections"]) == 2
        assert result["summary"]["total_revenue"] > 0
        assert result["summary"]["total_estimated_hours"] == 125.0  # 50 + 75

    async def test_calculate_sales_projection_monthly_breakdown(
        self, db_session, test_organization, test_service
    ):
        """Test monthly breakdown calculation"""
        test_service.default_margin_target = 0.30
        db_session.add(test_service)
        await db_session.commit()

        from app.models.team import TeamMember

        member = TeamMember(
            name="Test Member",
            role="Developer",
            salary_monthly_brute=5000.0,
            billable_hours_per_week=40,
            currency="USD",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(member)
        await db_session.commit()

        result = await calculate_sales_projection(
            db_session,
            test_organization.id,
            [test_service.id],
            {test_service.id: 120.0},  # 120 hours total
            win_rate=0.85,
            scenario="realistic",
            period_months=12,
            currency="USD",
        )

        # Should have 12 months
        assert len(result["monthly_projections"]) == 12

        # Each month should have revenue, costs, profit, margin
        for month_data in result["monthly_projections"]:
            assert "month" in month_data
            assert "revenue" in month_data
            assert "costs" in month_data
            assert "profit" in month_data
            assert "margin_percentage" in month_data
            assert month_data["revenue"] > 0
            assert month_data["costs"] > 0
            assert month_data["profit"] == month_data["revenue"] - month_data["costs"]

        # Hours per month should be 120 / 12 = 10
        assert result["summary"]["hours_per_month"] == 10.0
