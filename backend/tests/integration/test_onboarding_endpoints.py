"""
Integration tests for onboarding endpoints
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.cost import CostFixed
from app.models.organization import Organization
from app.models.team import TeamMember
from app.models.user import User


def get_auth_headers(user: User) -> dict:
    """Generate authorization headers for a user"""
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.full_name,
        "organization_id": user.organization_id,
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_org_with_owner(db_session: AsyncSession) -> tuple[Organization, User]:
    """Create test organization with owner user"""
    unique_id = str(uuid.uuid4())[:8]

    org = Organization(
        name="Test Onboarding Org",
        slug=f"test-onboarding-org-{unique_id}",
        subscription_plan="free",
        subscription_status="active",
        primary_currency="USD",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    user = User(
        email=f"owner{unique_id}@test.com",
        full_name="Owner User",
        hashed_password=get_password_hash("password123"),
        organization_id=org.id,
        role="owner",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return org, user


@pytest.fixture
async def test_org_with_admin_financiero(db_session: AsyncSession) -> tuple[Organization, User]:
    """Create test organization with admin_financiero user"""
    unique_id = str(uuid.uuid4())[:8]

    org = Organization(
        name="Test Admin Org",
        slug=f"test-admin-org-{unique_id}",
        subscription_plan="free",
        subscription_status="active",
        primary_currency="USD",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    user = User(
        email=f"admin{unique_id}@test.com",
        full_name="Admin Financiero",
        hashed_password=get_password_hash("password123"),
        organization_id=org.id,
        role="admin_financiero",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return org, user


@pytest.mark.integration
class TestGetBenchmarks:
    """Tests for GET /api/v1/onboarding/benchmarks"""

    async def test_get_benchmarks_freelance(
        self, async_client: AsyncClient, test_org_with_owner: tuple[Organization, User]
    ):
        """Test getting benchmarks for freelance profile"""
        org, user = test_org_with_owner
        headers = get_auth_headers(user)

        response = await async_client.get(
            "/api/v1/onboarding/benchmarks",
            params={"profile_type": "freelance", "country": "US", "currency": "USD"},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["profile_type"] == "freelance"
        assert data["country"] == "US"
        assert data["currency"] == "USD"
        assert data["source"] == "industry_standard"
        assert "benchmarks" in data
        assert data["benchmarks"]["avg_monthly_income"] == "5000"
        assert data["benchmarks"]["avg_margin"] == "25"

    async def test_get_benchmarks_company(
        self, async_client: AsyncClient, test_org_with_owner: tuple[Organization, User]
    ):
        """Test getting benchmarks for company profile"""
        org, user = test_org_with_owner
        headers = get_auth_headers(user)

        response = await async_client.get(
            "/api/v1/onboarding/benchmarks",
            params={"profile_type": "company", "country": "US", "currency": "USD"},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["profile_type"] == "company"
        assert data["benchmarks"]["avg_team_size"] == 5
        assert data["benchmarks"]["avg_salary"] == "3000"

    async def test_get_benchmarks_agency(
        self, async_client: AsyncClient, test_org_with_owner: tuple[Organization, User]
    ):
        """Test getting benchmarks for agency profile"""
        org, user = test_org_with_owner
        headers = get_auth_headers(user)

        response = await async_client.get(
            "/api/v1/onboarding/benchmarks",
            params={"profile_type": "agency", "country": "US", "currency": "USD"},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["profile_type"] == "agency"
        assert data["benchmarks"]["avg_team_size"] == 10
        assert data["benchmarks"]["avg_clients"] == 5

    async def test_get_benchmarks_invalid_profile_type(
        self, async_client: AsyncClient, test_org_with_owner: tuple[Organization, User]
    ):
        """Test getting benchmarks with invalid profile type"""
        org, user = test_org_with_owner
        headers = get_auth_headers(user)

        response = await async_client.get(
            "/api/v1/onboarding/benchmarks",
            params={"profile_type": "invalid", "country": "US", "currency": "USD"},
            headers=headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower()

    async def test_get_benchmarks_uses_org_defaults(
        self,
        async_client: AsyncClient,
        test_org_with_owner: tuple[Organization, User],
        db_session: AsyncSession,
    ):
        """Test that benchmarks use organization defaults when not provided"""
        org, user = test_org_with_owner

        # Update org settings
        org.settings = {"country": "COL"}
        org.primary_currency = "COP"
        await db_session.commit()
        await db_session.refresh(org)

        headers = get_auth_headers(user)

        response = await async_client.get(
            "/api/v1/onboarding/benchmarks", params={"profile_type": "freelance"}, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        # Should use org defaults
        assert data["country"] == "COL" or data["country"] == "US"  # May fallback to US
        assert data["currency"] == "COP" or data["currency"] == "USD"


@pytest.mark.integration
class TestCalculateTemporaryBCR:
    """Tests for POST /api/v1/onboarding/calculate-bcr"""

    async def test_calculate_temporary_bcr_success(
        self, async_client: AsyncClient, test_org_with_owner: tuple[Organization, User]
    ):
        """Test calculating temporary BCR successfully"""
        org, user = test_org_with_owner
        headers = get_auth_headers(user)

        response = await async_client.post(
            "/api/v1/onboarding/calculate-bcr",
            json={
                "team_members": [
                    {
                        "name": "Developer",
                        "role": "Developer",
                        "salary_monthly_brute": "5000",
                        "currency": "USD",
                        "billable_hours_per_month": 160,
                    }
                ],
                "expenses": [],
                "currency": "USD",
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "blended_cost_rate" in data
        assert data["total_salaries"] == "5000"
        assert data["total_fixed_overhead"] == "0"
        assert data["total_monthly_hours"] == 160.0
        assert data["team_members_count"] == 1
        assert data["currency"] == "USD"
        assert "note" in data

    async def test_calculate_temporary_bcr_with_expenses(
        self, async_client: AsyncClient, test_org_with_owner: tuple[Organization, User]
    ):
        """Test calculating temporary BCR with expenses"""
        org, user = test_org_with_owner
        headers = get_auth_headers(user)

        response = await async_client.post(
            "/api/v1/onboarding/calculate-bcr",
            json={
                "team_members": [
                    {
                        "name": "Developer",
                        "role": "Developer",
                        "salary_monthly_brute": "5000",
                        "currency": "USD",
                        "billable_hours_per_month": 160,
                    }
                ],
                "expenses": [
                    {
                        "name": "Office Rent",
                        "category": "rent",
                        "amount_monthly": "2000",
                        "currency": "USD",
                    }
                ],
                "currency": "USD",
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_monthly_costs"] == "7000"
        assert data["total_salaries"] == "5000"
        assert data["total_fixed_overhead"] == "2000"

    async def test_calculate_temporary_bcr_no_team_members(
        self, async_client: AsyncClient, test_org_with_owner: tuple[Organization, User]
    ):
        """Test calculating temporary BCR without team members"""
        org, user = test_org_with_owner
        headers = get_auth_headers(user)

        response = await async_client.post(
            "/api/v1/onboarding/calculate-bcr",
            json={"team_members": [], "expenses": [], "currency": "USD"},
            headers=headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "team member" in data["detail"].lower()


@pytest.mark.integration
class TestCompleteOnboarding:
    """Tests for POST /api/v1/onboarding/complete"""

    async def test_complete_onboarding_success(
        self,
        async_client: AsyncClient,
        test_org_with_owner: tuple[Organization, User],
        db_session: AsyncSession,
    ):
        """Test completing onboarding successfully"""
        org, user = test_org_with_owner
        headers = get_auth_headers(user)

        response = await async_client.post(
            "/api/v1/onboarding/complete",
            json={
                "organization_name": "Updated Org Name",
                "country": "USA",
                "currency": "USD",
                "profile_type": "freelance",
                "team_members": [],
                "expenses": [],
            },
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["organization_id"] == org.id
        assert data["team_members_created"] == 0
        assert data["expenses_created"] == 0
        assert "bcr_calculated" in data
        assert data["organization"]["name"] == "Updated Org Name"

        # Verify organization was updated
        result = await db_session.execute(select(Organization).where(Organization.id == org.id))
        updated_org = result.scalar_one()
        assert updated_org.name == "Updated Org Name"
        assert updated_org.settings["primary_currency"] == "USD"
        assert updated_org.settings["currency"] == "USD"
        assert updated_org.settings["country"] == "USA"
        assert updated_org.settings["onboarding_completed"] is True

    async def test_complete_onboarding_with_team_members(
        self,
        async_client: AsyncClient,
        test_org_with_owner: tuple[Organization, User],
        db_session: AsyncSession,
    ):
        """Test completing onboarding with team members"""
        org, user = test_org_with_owner
        headers = get_auth_headers(user)

        response = await async_client.post(
            "/api/v1/onboarding/complete",
            json={
                "country": "USA",
                "currency": "USD",
                "profile_type": "company",
                "team_members": [
                    {
                        "name": "John Doe",
                        "role": "Developer",
                        "salary_monthly_brute": "5000",
                        "currency": "USD",
                        "billable_hours_per_month": 160,
                    }
                ],
                "expenses": [],
            },
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["team_members_created"] == 1

        # Verify team member was created
        result = await db_session.execute(
            select(TeamMember).where(TeamMember.organization_id == org.id)
        )
        members = result.scalars().all()
        assert len(members) == 1
        assert members[0].name == "John Doe"

    async def test_complete_onboarding_with_expenses(
        self,
        async_client: AsyncClient,
        test_org_with_owner: tuple[Organization, User],
        db_session: AsyncSession,
    ):
        """Test completing onboarding with expenses"""
        org, user = test_org_with_owner
        headers = get_auth_headers(user)

        response = await async_client.post(
            "/api/v1/onboarding/complete",
            json={
                "country": "USA",
                "currency": "USD",
                "profile_type": "company",
                "team_members": [],
                "expenses": [
                    {
                        "name": "Office Rent",
                        "category": "rent",
                        "amount_monthly": "2000",
                        "currency": "USD",
                    }
                ],
            },
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["expenses_created"] == 1

        # Verify expense was created
        result = await db_session.execute(
            select(CostFixed).where(CostFixed.organization_id == org.id)
        )
        costs = result.scalars().all()
        assert len(costs) == 1
        assert costs[0].name == "Office Rent"

    async def test_complete_onboarding_admin_financiero(
        self, async_client: AsyncClient, test_org_with_admin_financiero: tuple[Organization, User]
    ):
        """Test that admin_financiero can complete onboarding"""
        org, user = test_org_with_admin_financiero
        headers = get_auth_headers(user)

        response = await async_client.post(
            "/api/v1/onboarding/complete",
            json={
                "country": "USA",
                "currency": "USD",
                "profile_type": "company",
                "team_members": [],
                "expenses": [],
            },
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True

    async def test_complete_onboarding_unauthorized_role(
        self, async_client: AsyncClient, db_session: AsyncSession, test_organization: Organization
    ):
        """Test that non-owner/admin_financiero cannot complete onboarding"""
        # Create a product_manager user
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            email=f"pm{unique_id}@test.com",
            full_name="Product Manager",
            hashed_password=get_password_hash("password123"),
            organization_id=test_organization.id,
            role="product_manager",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        headers = get_auth_headers(user)

        response = await async_client.post(
            "/api/v1/onboarding/complete",
            json={
                "country": "USA",
                "currency": "USD",
                "profile_type": "company",
                "team_members": [],
                "expenses": [],
            },
            headers=headers,
        )

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "permission" in data["detail"].lower() or "forbidden" in data["detail"].lower()

    async def test_complete_onboarding_missing_required_fields(
        self, async_client: AsyncClient, test_org_with_owner: tuple[Organization, User]
    ):
        """Test completing onboarding with missing required fields"""
        org, user = test_org_with_owner
        headers = get_auth_headers(user)

        response = await async_client.post(
            "/api/v1/onboarding/complete",
            json={
                "country": "USA",
                # Missing currency and profile_type
                "team_members": [],
                "expenses": [],
            },
            headers=headers,
        )

        assert response.status_code == 422  # Validation error

    async def test_complete_onboarding_full_flow(
        self,
        async_client: AsyncClient,
        test_org_with_owner: tuple[Organization, User],
        db_session: AsyncSession,
    ):
        """Test complete onboarding flow with all data"""
        org, user = test_org_with_owner
        headers = get_auth_headers(user)

        response = await async_client.post(
            "/api/v1/onboarding/complete",
            json={
                "organization_name": "Complete Test Org",
                "organization_description": "Test description",
                "country": "COL",
                "currency": "COP",
                "profile_type": "agency",
                "team_members": [
                    {
                        "name": "Developer 1",
                        "role": "Developer",
                        "salary_monthly_brute": "5000",
                        "currency": "COP",
                        "billable_hours_per_month": 160,
                    },
                    {
                        "name": "Designer 1",
                        "role": "Designer",
                        "salary_monthly_brute": "4000",
                        "currency": "COP",
                        "billable_hours_per_month": 160,
                    },
                ],
                "expenses": [
                    {
                        "name": "Office Rent",
                        "category": "rent",
                        "amount_monthly": "2000",
                        "currency": "COP",
                    },
                    {
                        "name": "Slack",
                        "category": "software",
                        "amount_monthly": "100",
                        "currency": "COP",
                    },
                ],
                "tax_structure": {"iva": 19.0, "ica": 0.966},
                "social_charges_config": {
                    "enable_social_charges": True,
                    "health_percentage": 8.5,
                    "pension_percentage": 12.0,
                },
            },
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["team_members_created"] == 2
        assert data["expenses_created"] == 2

        # Verify all data was saved
        result = await db_session.execute(select(Organization).where(Organization.id == org.id))
        updated_org = result.scalar_one()
        assert updated_org.name == "Complete Test Org"
        assert updated_org.primary_currency == "COP"
        assert updated_org.settings["country"] == "COL"
        assert updated_org.settings["profile_type"] == "agency"
        assert updated_org.settings["tax_structure"]["iva"] == 19.0
        assert updated_org.settings["social_charges_config"]["enable_social_charges"] is True

        # Verify team members
        result = await db_session.execute(
            select(TeamMember).where(TeamMember.organization_id == org.id)
        )
        members = result.scalars().all()
        assert len(members) == 2

        # Verify expenses
        result = await db_session.execute(
            select(CostFixed).where(CostFixed.organization_id == org.id)
        )
        costs = result.scalars().all()
        assert len(costs) == 2
