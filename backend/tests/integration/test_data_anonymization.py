"""
Integration tests for data anonymization service

Tests verify that sensitive data is properly anonymized for support roles.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.project import Project, Quote
from app.models.team import TeamMember
from app.services.data_anonymizer import (
    anonymize_amount,
    anonymize_blended_rate,
    anonymize_client_name,
    anonymize_name,
    anonymize_percentage,
    anonymize_project_cost_data,
    anonymize_quote_totals,
    anonymize_team_salaries,
    anonymize_usage_metrics,
)


@pytest.fixture
async def test_org(db_session: AsyncSession) -> Organization:
    """Create test organization"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    org = Organization(
        name="Test Organization",
        slug=f"test-org-{unique_id}",
        subscription_plan="professional",
        subscription_status="active",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def test_project(db_session: AsyncSession, test_org: Organization) -> Project:
    """Create test project"""
    project = Project(
        name="Test Project",
        client_name="Test Client Inc",
        client_email="client@test.com",
        status="Draft",
        currency="USD",
        organization_id=test_org.id,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def test_quote(db_session: AsyncSession, test_project: Project) -> Quote:
    """Create test quote"""
    quote = Quote(
        project_id=test_project.id,
        version=1,
        total_internal_cost=5000.0,
        total_client_price=8000.0,
        margin_percentage=0.375,
        notes="Test quote",
    )
    db_session.add(quote)
    await db_session.commit()
    await db_session.refresh(quote)
    return quote


@pytest.fixture
async def test_team_member(db_session: AsyncSession, test_org: Organization) -> TeamMember:
    """Create test team member"""
    member = TeamMember(
        name="John Doe",
        role="Developer",
        salary_monthly_brute=6000.0,
        currency="USD",
        billable_hours_per_week=40,
        is_active=True,
        organization_id=test_org.id,
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)
    return member


@pytest.mark.integration
class TestBlendedRateAnonymization:
    """Tests for blended rate anonymization"""

    def test_anonymize_blended_rate_low(self):
        """Test anonymization of low blended rates"""
        assert anonymize_blended_rate(25.0) == "USD0-50"
        assert anonymize_blended_rate(45.0) == "USD0-50"

    def test_anonymize_blended_rate_medium(self):
        """Test anonymization of medium blended rates"""
        assert anonymize_blended_rate(75.0) == "USD50-100"
        assert anonymize_blended_rate(95.0) == "USD50-100"

    def test_anonymize_blended_rate_high(self):
        """Test anonymization of high blended rates"""
        assert anonymize_blended_rate(125.0) == "USD100-150"
        assert anonymize_blended_rate(175.0) == "USD150-200"
        assert anonymize_blended_rate(250.0) == "USD200+"


@pytest.mark.integration
class TestAmountAnonymization:
    """Tests for amount anonymization"""

    def test_anonymize_amount_small(self):
        """Test anonymization of small amounts"""
        assert anonymize_amount(500.0) == "USD0-1K"
        assert anonymize_amount(999.0) == "USD0-1K"

    def test_anonymize_amount_medium(self):
        """Test anonymization of medium amounts"""
        assert anonymize_amount(2000.0) == "USD1K-5K"
        assert anonymize_amount(8000.0) == "USD5K-10K"
        assert anonymize_amount(20000.0) == "USD10K-25K"

    def test_anonymize_amount_large(self):
        """Test anonymization of large amounts"""
        assert anonymize_amount(30000.0) == "USD25K-50K"
        assert anonymize_amount(50000.0) == "USD50K-100K"
        assert anonymize_amount(75000.0) == "USD50K-100K"
        assert anonymize_amount(150000.0) == "USD100K+"


@pytest.mark.integration
class TestPercentageAnonymization:
    """Tests for percentage anonymization"""

    def test_anonymize_percentage_0_to_1_format(self):
        """Test anonymization with 0-1 format"""
        assert anonymize_percentage(0.15) == "10-20%"  # 15%
        assert anonymize_percentage(0.35) == "30-40%"  # 35%
        assert anonymize_percentage(0.55) == "50%+"  # 55%

    def test_anonymize_percentage_0_to_100_format(self):
        """Test anonymization with 0-100 format"""
        assert anonymize_percentage(15.0) == "10-20%"
        assert anonymize_percentage(35.0) == "30-40%"
        assert anonymize_percentage(55.0) == "50%+"


@pytest.mark.integration
class TestNameAnonymization:
    """Tests for name anonymization"""

    def test_anonymize_client_name(self):
        """Test client name anonymization"""
        assert anonymize_client_name("Test Client") == "T*****"
        assert anonymize_client_name("A") == "A**"
        assert anonymize_client_name("") == "***"
        assert anonymize_client_name("ABC") == "A**"

    def test_anonymize_person_name(self):
        """Test person name anonymization"""
        assert anonymize_name("John Doe") == "J*** D***"
        assert anonymize_name("Jane") == "J***"
        assert anonymize_name("") == "***"
        assert anonymize_name("Mary Jane Watson") == "M*** W***"  # Uses last name


@pytest.mark.integration
class TestQuoteAnonymization:
    """Tests for quote anonymization"""

    async def test_anonymize_quote_totals(self, test_quote: Quote):
        """Test quote totals anonymization"""
        anonymized = anonymize_quote_totals(test_quote, "USD")

        assert anonymized["id"] == test_quote.id
        assert anonymized["project_id"] == test_quote.project_id
        assert anonymized["version"] == test_quote.version
        # Amounts should be anonymized (ranges, not exact values)
        assert isinstance(anonymized["total_internal_cost"], str)
        assert "USD" in anonymized["total_internal_cost"]
        assert isinstance(anonymized["total_client_price"], str)
        assert "USD" in anonymized["total_client_price"]
        # Percentage should be anonymized
        assert isinstance(anonymized["margin_percentage"], str)
        assert "%" in anonymized["margin_percentage"]


@pytest.mark.integration
class TestProjectAnonymization:
    """Tests for project anonymization"""

    async def test_anonymize_project_cost_data(
        self,
        db_session: AsyncSession,
        test_org: Organization,
        test_project: Project,
        test_quote: Quote,
    ):
        """Test project cost data anonymization"""
        # Load quotes relationship
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        project_result = await db_session.execute(
            select(Project)
            .options(selectinload(Project.quotes))
            .where(Project.id == test_project.id)
        )
        project = project_result.scalar_one()

        anonymized = anonymize_project_cost_data(project, "USD")

        assert anonymized["id"] == project.id
        assert anonymized["name"] == project.name
        # Client name should be anonymized
        assert anonymized["client_name"] != project.client_name
        assert anonymized["client_name"].startswith("T")
        assert "*" in anonymized["client_name"]
        assert anonymized["status"] == project.status
        assert anonymized["currency"] == "USD"
        # Latest quote should be anonymized if present
        if anonymized.get("latest_quote"):
            assert isinstance(anonymized["latest_quote"]["total_internal_cost"], str)


@pytest.mark.integration
class TestTeamSalariesAnonymization:
    """Tests for team salary anonymization"""

    async def test_anonymize_team_salaries(self, test_team_member: TeamMember):
        """Test team salary anonymization"""
        members = [test_team_member]
        anonymized = anonymize_team_salaries(members, "USD")

        assert len(anonymized) == 1
        member_data = anonymized[0]

        assert member_data["id"] == test_team_member.id
        # Name should be anonymized
        assert member_data["name"] != test_team_member.name
        assert "*" in member_data["name"]
        assert member_data["role"] == test_team_member.role
        # Salary should be anonymized (range, not exact value)
        assert isinstance(member_data["salary_monthly_brute"], str)
        assert "USD" in member_data["salary_monthly_brute"]
        assert member_data["billable_hours_per_week"] == test_team_member.billable_hours_per_week
        assert member_data["is_active"] == test_team_member.is_active


@pytest.mark.integration
class TestUsageMetricsAnonymization:
    """Tests for usage metrics anonymization"""

    def test_anonymize_usage_metrics_zero(self):
        """Test anonymization of zero counts"""
        result = anonymize_usage_metrics(0, 0, 0)
        assert result["user_count"] == "0"
        assert result["project_count"] == "0"
        assert result["quote_count"] == "0"

    def test_anonymize_usage_metrics_small(self):
        """Test anonymization of small counts"""
        result = anonymize_usage_metrics(3, 7, 12)
        assert result["user_count"] == "1-5"
        assert result["project_count"] == "5-10"
        assert result["quote_count"] == "10-25"

    def test_anonymize_usage_metrics_large(self):
        """Test anonymization of large counts"""
        result = anonymize_usage_metrics(100, 50, 200)
        assert result["user_count"] == "50+"
        assert result["project_count"] == "50+"
        assert result["quote_count"] == "50+"

    def test_anonymize_usage_metrics_with_credits(self):
        """Test anonymization with credit information"""
        result = anonymize_usage_metrics(
            user_count=10,
            project_count=25,
            quote_count=50,
            credits_available=100,
            credits_used_this_month=30,
        )
        assert result["user_count"] == "10-25"
        assert result["credits_available"] == "50+"
        assert result["credits_used_this_month"] == "25-50"
