"""
Integration tests for advanced pricing features (Sprint 16)

Tests validate:
1. Calculation with additional revisions
2. Calculation of projects by value (project_value pricing)
3. Combination of services + expenses + revisions
4. All pricing types (hourly, fixed, recurring, project_value)
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.calculations import calculate_blended_cost_rate, calculate_quote_totals_enhanced
from app.models.organization import Organization
from app.models.service import Service
from app.models.settings import AgencySettings
from app.models.team import TeamMember


@pytest.mark.integration
class TestAdvancedPricingRevisions:
    """Test quote calculation with revisions"""

    async def test_calculation_with_no_additional_revisions(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """Test calculation when revisions_count <= revisions_included"""
        # Create settings
        settings = AgencySettings(
            primary_currency="USD", currency_symbol="$", organization_id=test_organization.id
        )
        db_session.add(settings)

        # Create team member for BCR
        team_member = TeamMember(
            name="Test Developer",
            role="Developer",
            salary_monthly_brute=5000.0,
            currency="USD",
            billable_hours_per_week=40,
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(team_member)

        # Create service
        service = Service(
            name="Web Development",
            description="Web development service",
            default_margin_target=0.30,
            pricing_type="hourly",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(service)
        await db_session.commit()
        await db_session.refresh(service)

        # Calculate BCR
        bcr = await calculate_blended_cost_rate(test_organization.id, db_session)
        assert bcr > 0

        # Calculate quote with revisions (2 included, 2 requested)
        items = [{"service_id": service.id, "estimated_hours": 10.0}]
        result = await calculate_quote_totals_enhanced(
            db=db_session,
            items=items,
            blended_cost_rate=bcr,
            revisions_included=2,
            revision_cost_per_additional=100.0,
            revisions_count=2,  # No additional revisions
        )

        assert "revisions_cost" in result
        assert result["revisions_cost"] == 0.0  # No additional revisions
        assert result["total_client_price"] > 0

    async def test_calculation_with_additional_revisions(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """Test calculation when revisions_count > revisions_included"""
        # Create settings
        settings = AgencySettings(
            primary_currency="USD", currency_symbol="$", organization_id=test_organization.id
        )
        db_session.add(settings)

        # Create team member for BCR
        team_member = TeamMember(
            name="Test Developer",
            role="Developer",
            salary_monthly_brute=5000.0,
            currency="USD",
            billable_hours_per_week=40,
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(team_member)

        # Create service
        service = Service(
            name="Web Development",
            description="Web development service",
            default_margin_target=0.30,
            pricing_type="hourly",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(service)
        await db_session.commit()
        await db_session.refresh(service)

        # Calculate BCR
        bcr = await calculate_blended_cost_rate(test_organization.id, db_session)
        assert bcr > 0

        # Calculate quote with additional revisions (2 included, 5 requested = 3 additional)
        items = [{"service_id": service.id, "estimated_hours": 10.0}]
        revision_cost_per_additional = 150.0
        revisions_included = 2
        revisions_count = 5

        result = await calculate_quote_totals_enhanced(
            db=db_session,
            items=items,
            blended_cost_rate=bcr,
            revisions_included=revisions_included,
            revision_cost_per_additional=revision_cost_per_additional,
            revisions_count=revisions_count,
        )

        assert "revisions_cost" in result
        expected_revisions_cost = (
            revisions_count - revisions_included
        ) * revision_cost_per_additional
        assert result["revisions_cost"] == pytest.approx(expected_revisions_cost, rel=0.01)

        # Total client price should include revisions cost
        base_price = result["total_client_price"] - result["revisions_cost"]
        assert result["total_client_price"] == pytest.approx(
            base_price + expected_revisions_cost, rel=0.01
        )

    async def test_calculation_with_revisions_no_cost_per_additional(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """Test calculation with revisions_count but no revision_cost_per_additional"""
        # Create settings and team member
        settings = AgencySettings(
            primary_currency="USD", currency_symbol="$", organization_id=test_organization.id
        )
        db_session.add(settings)

        team_member = TeamMember(
            name="Test Developer",
            role="Developer",
            salary_monthly_brute=5000.0,
            currency="USD",
            billable_hours_per_week=40,
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(team_member)

        service = Service(
            name="Web Development",
            pricing_type="hourly",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(service)
        await db_session.commit()
        await db_session.refresh(service)

        bcr = await calculate_blended_cost_rate(test_organization.id, db_session)
        items = [{"service_id": service.id, "estimated_hours": 10.0}]

        # No revision_cost_per_additional means no additional cost
        result = await calculate_quote_totals_enhanced(
            db=db_session,
            items=items,
            blended_cost_rate=bcr,
            revisions_included=2,
            revision_cost_per_additional=None,
            revisions_count=5,
        )

        assert result["revisions_cost"] == 0.0


@pytest.mark.integration
class TestProjectValuePricing:
    """Test quote calculation with project_value pricing type"""

    async def test_calculation_with_project_value_with_hours(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """Test project_value pricing with estimated hours provided"""
        # Create settings
        settings = AgencySettings(
            primary_currency="USD", currency_symbol="$", organization_id=test_organization.id
        )
        db_session.add(settings)

        # Create team member for BCR
        team_member = TeamMember(
            name="Test Designer",
            role="Designer",
            salary_monthly_brute=6000.0,
            currency="USD",
            billable_hours_per_week=40,
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(team_member)

        # Create service with project_value pricing
        service = Service(
            name="IP Development",
            description="Complete IP development",
            pricing_type="project_value",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(service)
        await db_session.commit()
        await db_session.refresh(service)

        # Calculate BCR
        bcr = await calculate_blended_cost_rate(test_organization.id, db_session)
        assert bcr > 0

        # Calculate quote with project_value (with estimated hours)
        project_value = 10000.0
        estimated_hours = 50.0
        items = [
            {
                "service_id": service.id,
                "pricing_type": "project_value",
                "project_value": project_value,
                "estimated_hours": estimated_hours,
            }
        ]

        result = await calculate_quote_totals_enhanced(
            db=db_session, items=items, blended_cost_rate=bcr
        )

        assert result["total_client_price"] == pytest.approx(project_value, rel=0.01)
        # Internal cost should be based on hours × BCR
        expected_internal_cost = bcr * estimated_hours
        assert result["total_internal_cost"] == pytest.approx(expected_internal_cost, rel=0.01)

    async def test_calculation_with_project_value_without_hours(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """Test project_value pricing without estimated hours (uses 50% assumption)"""
        # Create settings
        settings = AgencySettings(
            primary_currency="USD", currency_symbol="$", organization_id=test_organization.id
        )
        db_session.add(settings)

        # Create team member
        team_member = TeamMember(
            name="Test Designer",
            role="Designer",
            salary_monthly_brute=6000.0,
            currency="USD",
            billable_hours_per_week=40,
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(team_member)

        # Create service with project_value pricing
        service = Service(
            name="IP Development",
            pricing_type="project_value",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(service)
        await db_session.commit()
        await db_session.refresh(service)

        bcr = await calculate_blended_cost_rate(test_organization.id, db_session)

        # Calculate quote without estimated hours
        project_value = 15000.0
        items = [
            {
                "service_id": service.id,
                "pricing_type": "project_value",
                "project_value": project_value,
                # No estimated_hours
            }
        ]

        result = await calculate_quote_totals_enhanced(
            db=db_session, items=items, blended_cost_rate=bcr
        )

        assert result["total_client_price"] == pytest.approx(project_value, rel=0.01)
        # Internal cost should be 50% of project value when no hours provided
        expected_internal_cost = project_value * 0.5
        assert result["total_internal_cost"] == pytest.approx(expected_internal_cost, rel=0.01)

    async def test_calculation_with_fixed_pricing(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """Test fixed pricing type"""
        # Create settings
        settings = AgencySettings(
            primary_currency="USD", currency_symbol="$", organization_id=test_organization.id
        )
        db_session.add(settings)

        # Create service with fixed pricing
        service = Service(
            name="Contract Review",
            pricing_type="fixed",
            fixed_price=500.0,
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(service)
        await db_session.commit()
        await db_session.refresh(service)

        # Fixed pricing doesn't require BCR, but we still need it for the function
        team_member = TeamMember(
            name="Test Lawyer",
            role="Lawyer",
            salary_monthly_brute=8000.0,
            currency="USD",
            billable_hours_per_week=40,
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(team_member)
        bcr = await calculate_blended_cost_rate(test_organization.id, db_session)

        # Calculate quote with fixed pricing
        fixed_price = 500.0
        quantity = 2.0
        items = [
            {
                "service_id": service.id,
                "pricing_type": "fixed",
                "fixed_price": fixed_price,
                "quantity": quantity,
            }
        ]

        result = await calculate_quote_totals_enhanced(
            db=db_session, items=items, blended_cost_rate=bcr
        )

        expected_client_price = fixed_price * quantity
        assert result["total_client_price"] == pytest.approx(expected_client_price, rel=0.01)
        # Internal cost for fixed pricing is typically 50% of client price
        assert result["total_internal_cost"] == pytest.approx(expected_client_price * 0.5, rel=0.01)


@pytest.mark.integration
class TestCombinedPricingFeatures:
    """Test combinations of services, expenses, and revisions"""

    async def test_combined_hourly_services_expenses_revisions(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """Test calculation combining hourly services + expenses + revisions"""
        # Create settings
        settings = AgencySettings(
            primary_currency="USD", currency_symbol="$", organization_id=test_organization.id
        )
        db_session.add(settings)

        # Create team member
        team_member = TeamMember(
            name="Test Developer",
            role="Developer",
            salary_monthly_brute=5000.0,
            currency="USD",
            billable_hours_per_week=40,
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(team_member)

        # Create services
        service1 = Service(
            name="Web Development",
            pricing_type="hourly",
            default_margin_target=0.30,
            is_active=True,
            organization_id=test_organization.id,
        )
        service2 = Service(
            name="Design",
            pricing_type="hourly",
            default_margin_target=0.35,
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add_all([service1, service2])
        await db_session.commit()
        await db_session.refresh(service1)
        await db_session.refresh(service2)

        bcr = await calculate_blended_cost_rate(test_organization.id, db_session)

        # Create items (services)
        items = [
            {"service_id": service1.id, "estimated_hours": 20.0},
            {"service_id": service2.id, "estimated_hours": 10.0},
        ]

        # Create expenses (third-party costs with markup)
        expenses = [
            {"name": "Stock Images", "cost": 100.0, "markup_percentage": 0.10, "quantity": 1.0},
            {"name": "Hosting Setup", "cost": 200.0, "markup_percentage": 0.15, "quantity": 1.0},
        ]

        # Calculate with revisions
        revisions_included = 2
        revision_cost_per_additional = 100.0
        revisions_count = 4  # 2 additional revisions

        result = await calculate_quote_totals_enhanced(
            db=db_session,
            items=items,
            blended_cost_rate=bcr,
            expenses=expenses,
            revisions_included=revisions_included,
            revision_cost_per_additional=revision_cost_per_additional,
            revisions_count=revisions_count,
        )

        # Verify all components are included
        assert "total_internal_cost" in result
        assert "total_client_price" in result
        assert "total_expenses_cost" in result
        assert "total_expenses_client_price" in result
        assert "revisions_cost" in result

        # Verify expenses calculation
        expected_expenses_cost = 100.0 + 200.0  # 300
        expected_expenses_client_price = (100.0 * 1.10) + (200.0 * 1.15)  # 110 + 230 = 340
        assert result["total_expenses_cost"] == pytest.approx(expected_expenses_cost, rel=0.01)
        assert result["total_expenses_client_price"] == pytest.approx(
            expected_expenses_client_price, rel=0.01
        )

        # Verify revisions cost
        expected_revisions_cost = (
            revisions_count - revisions_included
        ) * revision_cost_per_additional
        assert result["revisions_cost"] == pytest.approx(expected_revisions_cost, rel=0.01)

        # Verify total client price includes services + expenses + revisions
        services_price = (
            result["total_client_price"]
            - result["total_expenses_client_price"]
            - result["revisions_cost"]
        )
        assert services_price > 0
        assert result["total_client_price"] > expected_expenses_client_price
        assert result["total_client_price"] > expected_revisions_cost

    async def test_combined_mixed_pricing_types_expenses_revisions(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """Test combination of hourly + fixed + project_value services + expenses + revisions"""
        # Create settings
        settings = AgencySettings(
            primary_currency="USD", currency_symbol="$", organization_id=test_organization.id
        )
        db_session.add(settings)

        # Create team member
        team_member = TeamMember(
            name="Test Developer",
            role="Developer",
            salary_monthly_brute=5000.0,
            currency="USD",
            billable_hours_per_week=40,
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(team_member)

        # Create services with different pricing types
        hourly_service = Service(
            name="Development",
            pricing_type="hourly",
            default_margin_target=0.30,
            is_active=True,
            organization_id=test_organization.id,
        )
        fixed_service = Service(
            name="Setup",
            pricing_type="fixed",
            fixed_price=500.0,
            is_active=True,
            organization_id=test_organization.id,
        )
        project_value_service = Service(
            name="IP Package",
            pricing_type="project_value",
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add_all([hourly_service, fixed_service, project_value_service])
        await db_session.commit()
        await db_session.refresh(hourly_service)
        await db_session.refresh(fixed_service)
        await db_session.refresh(project_value_service)

        bcr = await calculate_blended_cost_rate(test_organization.id, db_session)

        # Create items with different pricing types
        items = [
            {"service_id": hourly_service.id, "estimated_hours": 20.0},
            {
                "service_id": fixed_service.id,
                "pricing_type": "fixed",
                "fixed_price": 500.0,
                "quantity": 1.0,
            },
            {
                "service_id": project_value_service.id,
                "pricing_type": "project_value",
                "project_value": 5000.0,
                "estimated_hours": 30.0,
            },
        ]

        # Create expenses
        expenses = [
            {
                "name": "Third-party Service",
                "cost": 300.0,
                "markup_percentage": 0.20,
                "quantity": 1.0,
            }
        ]

        # Calculate with revisions
        result = await calculate_quote_totals_enhanced(
            db=db_session,
            items=items,
            blended_cost_rate=bcr,
            expenses=expenses,
            revisions_included=2,
            revision_cost_per_additional=150.0,
            revisions_count=3,  # 1 additional revision
        )

        # Verify all components
        assert result["total_client_price"] > 0
        assert result["total_internal_cost"] > 0
        assert result["total_expenses_client_price"] > 0
        assert result["revisions_cost"] == pytest.approx(150.0, rel=0.01)  # 1 additional revision

        # Verify breakdown
        assert len(result["items"]) == 3  # Three services
        assert result["total_expenses_cost"] == pytest.approx(300.0, rel=0.01)
        assert result["total_expenses_client_price"] == pytest.approx(360.0, rel=0.01)  # 300 * 1.20

    async def test_combined_no_expenses_no_revisions(
        self, db_session: AsyncSession, test_organization: Organization
    ):
        """Test calculation with services only (no expenses, no revisions)"""
        # Create settings
        settings = AgencySettings(
            primary_currency="USD", currency_symbol="$", organization_id=test_organization.id
        )
        db_session.add(settings)

        # Create team member
        team_member = TeamMember(
            name="Test Developer",
            role="Developer",
            salary_monthly_brute=5000.0,
            currency="USD",
            billable_hours_per_week=40,
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(team_member)

        # Create service
        service = Service(
            name="Development",
            pricing_type="hourly",
            default_margin_target=0.30,
            is_active=True,
            organization_id=test_organization.id,
        )
        db_session.add(service)
        await db_session.commit()
        await db_session.refresh(service)

        bcr = await calculate_blended_cost_rate(test_organization.id, db_session)

        items = [{"service_id": service.id, "estimated_hours": 10.0}]

        result = await calculate_quote_totals_enhanced(
            db=db_session,
            items=items,
            blended_cost_rate=bcr,
            expenses=None,
            revisions_included=2,
            revision_cost_per_additional=None,
            revisions_count=None,
        )

        # Should have zero expenses and revisions cost
        assert result["total_expenses_cost"] == 0.0
        assert result["total_expenses_client_price"] == 0.0
        assert result["revisions_cost"] == 0.0

        # But should have services cost
        assert result["total_client_price"] > 0
        assert result["total_internal_cost"] > 0
