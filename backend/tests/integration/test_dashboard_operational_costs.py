"""
Integration tests for GET /api/v1/dashboard/operational-costs.
Covers permissions (owner, admin_financiero, super_admin), tenant isolation, and response schema.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.cost import CostFixed
from app.models.organization import Organization
from app.models.team import TeamMember
from app.models.user import User
from tests.auth_helpers import get_auth_headers


@pytest.fixture
async def org_with_data(db_session: AsyncSession) -> Organization:
    """Create organization with team member and fixed cost for operational cost data."""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    org = Organization(
        name="OpCost Org",
        slug=f"opcost-org-{unique_id}",
        subscription_plan="free",
        subscription_status="active",
    )
    db_session.add(org)
    await db_session.flush()

    user = User(
        email=f"owner-{unique_id}@test.com",
        full_name="Owner",
        hashed_password=get_password_hash("test123"),
        role="owner",
        role_type="tenant",
        organization_id=org.id,
    )
    db_session.add(user)
    await db_session.flush()

    member = TeamMember(
        user_id=user.id,
        name="Member",
        role="Dev",
        salary_monthly_brute=3000,
        currency="USD",
        billable_hours_per_week=40,
        is_active=True,
        organization_id=org.id,
    )
    db_session.add(member)

    cost = CostFixed(
        name="Rent",
        amount_monthly=500,
        currency="USD",
        category="Overhead",
        organization_id=org.id,
    )
    db_session.add(cost)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def users_operational(db_session: AsyncSession, org_with_data: Organization) -> dict:
    """Create owner, admin_financiero, super_admin, and collaborator (no access)."""
    import uuid

    uid = str(uuid.uuid4())[:8]
    password_hash = get_password_hash("test123")
    users = {
        "owner": User(
            email=f"owner-op-{uid}@test.com",
            full_name="Owner",
            hashed_password=password_hash,
            role="owner",
            role_type="tenant",
            organization_id=org_with_data.id,
        ),
        "admin_financiero": User(
            email=f"admin-op-{uid}@test.com",
            full_name="Admin Fin",
            hashed_password=password_hash,
            role="admin_financiero",
            role_type="tenant",
            organization_id=org_with_data.id,
        ),
        "super_admin": User(
            email=f"super-op-{uid}@test.com",
            full_name="Super",
            hashed_password=password_hash,
            role="super_admin",
            role_type="support",
            organization_id=org_with_data.id,
        ),
        "collaborator": User(
            email=f"collab-op-{uid}@test.com",
            full_name="Collab",
            hashed_password=password_hash,
            role="collaborator",
            role_type="tenant",
            organization_id=org_with_data.id,
        ),
    }
    for u in users.values():
        db_session.add(u)
    await db_session.commit()
    for u in users.values():
        await db_session.refresh(u)
    return users


@pytest.mark.integration
class TestDashboardOperationalCostsEndpoint:
    """Test GET /api/v1/dashboard/operational-costs."""

    async def test_owner_can_access(
        self,
        async_client: AsyncClient,
        users_operational: dict,
    ):
        headers = get_auth_headers(users_operational["owner"])
        response = await async_client.get(
            "/api/v1/dashboard/operational-costs?period=current_month",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "resource_costs" in data
        assert "fixed_costs" in data
        assert "amortization" in data
        assert "tax_costs" in data
        assert "total_operational_cost" in data
        assert "calculation_metadata" in data
        assert "data_integrity_ok" in data
        assert data["calculation_metadata"]["currency"] == "USD"
        assert "calculation_id" in data["calculation_metadata"]

    async def test_admin_financiero_can_access(
        self,
        async_client: AsyncClient,
        users_operational: dict,
    ):
        headers = get_auth_headers(users_operational["admin_financiero"])
        response = await async_client.get(
            "/api/v1/dashboard/operational-costs?period=current_month",
            headers=headers,
        )
        assert response.status_code == 200

    async def test_super_admin_can_access(
        self,
        async_client: AsyncClient,
        users_operational: dict,
    ):
        headers = get_auth_headers(users_operational["super_admin"])
        response = await async_client.get(
            "/api/v1/dashboard/operational-costs?period=current_month",
            headers=headers,
        )
        assert response.status_code == 200

    async def test_super_admin_can_access_with_explicit_organization_id(
        self,
        async_client: AsyncClient,
        users_operational: dict,
        org_with_data: Organization,
    ):
        headers = get_auth_headers(users_operational["super_admin"])
        response = await async_client.get(
            f"/api/v1/dashboard/operational-costs?period=current_month&organization_id={org_with_data.id}",
            headers=headers,
        )
        assert response.status_code == 200

    async def test_super_admin_without_org_must_send_organization_id(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        import uuid

        uid = str(uuid.uuid4())[:8]
        super_admin = User(
            email=f"super-no-org-{uid}@test.com",
            full_name="Super No Org",
            hashed_password=get_password_hash("test123"),
            role="super_admin",
            role_type="support",
            organization_id=None,
        )
        db_session.add(super_admin)
        await db_session.commit()
        await db_session.refresh(super_admin)

        headers = get_auth_headers(super_admin)
        response = await async_client.get(
            "/api/v1/dashboard/operational-costs?period=current_month",
            headers=headers,
        )
        assert response.status_code == 400

    async def test_collaborator_forbidden(
        self,
        async_client: AsyncClient,
        users_operational: dict,
    ):
        headers = get_auth_headers(users_operational["collaborator"])
        response = await async_client.get(
            "/api/v1/dashboard/operational-costs?period=current_month",
            headers=headers,
        )
        assert response.status_code == 403

    async def test_invalid_period(
        self,
        async_client: AsyncClient,
        users_operational: dict,
    ):
        headers = get_auth_headers(users_operational["owner"])
        response = await async_client.get(
            "/api/v1/dashboard/operational-costs?period=last_year",
            headers=headers,
        )
        assert response.status_code == 400

    async def test_totals_consistency(
        self,
        async_client: AsyncClient,
        users_operational: dict,
    ):
        headers = get_auth_headers(users_operational["owner"])
        response = await async_client.get(
            "/api/v1/dashboard/operational-costs?period=current_month",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        rc = float(data["resource_costs"])
        fc = float(data["fixed_costs"])
        am = float(data["amortization"])
        tc = float(data["tax_costs"])
        total = float(data["total_operational_cost"])
        assert abs(total - (rc + fc + am + tc)) < 0.01

    async def test_unauthenticated_forbidden(self, async_client: AsyncClient):
        response = await async_client.get(
            "/api/v1/dashboard/operational-costs?period=current_month"
        )
        assert response.status_code == 401

    async def test_negative_fixed_cost_returns_400(
        self,
        async_client: AsyncClient,
        users_operational: dict,
        db_session: AsyncSession,
        org_with_data: Organization,
    ):
        invalid_cost = CostFixed(
            name="Invalid negative",
            amount_monthly=-100,
            currency="USD",
            category="Overhead",
            organization_id=org_with_data.id,
        )
        db_session.add(invalid_cost)
        await db_session.commit()

        headers = get_auth_headers(users_operational["owner"])
        response = await async_client.get(
            "/api/v1/dashboard/operational-costs?period=current_month",
            headers=headers,
        )
        assert response.status_code == 400

    async def test_empty_period_data_returns_zeroes(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        import uuid

        uid = str(uuid.uuid4())[:8]
        org = Organization(
            name=f"Empty Org {uid}",
            slug=f"empty-org-{uid}",
            subscription_plan="free",
            subscription_status="active",
        )
        owner = User(
            email=f"owner-empty-{uid}@test.com",
            full_name="Owner Empty",
            hashed_password=get_password_hash("test123"),
            role="owner",
            role_type="tenant",
            organization=org,
        )
        db_session.add_all([org, owner])
        await db_session.commit()
        await db_session.refresh(owner)

        response = await async_client.get(
            "/api/v1/dashboard/operational-costs?period=current_month",
            headers=get_auth_headers(owner),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resource_costs"] == "0"
        assert data["fixed_costs"] == "0.0000"
        assert data["amortization"] == "0.0000"
        assert data["tax_costs"] == "0.0000"
        assert data["effective_margin_observed"] is None

    async def test_zero_hours_team_member_does_not_break_endpoint(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
    ):
        import uuid

        uid = str(uuid.uuid4())[:8]
        org = Organization(
            name=f"Zero Hours Org {uid}",
            slug=f"zero-hours-org-{uid}",
            subscription_plan="free",
            subscription_status="active",
        )
        owner = User(
            email=f"owner-zero-{uid}@test.com",
            full_name="Owner Zero",
            hashed_password=get_password_hash("test123"),
            role="owner",
            role_type="tenant",
            organization=org,
        )
        db_session.add_all([org, owner])
        await db_session.flush()
        member = TeamMember(
            user_id=owner.id,
            name="Zero Hours Member",
            role="Dev",
            salary_monthly_brute=2500,
            currency="USD",
            billable_hours_per_week=0,
            is_active=True,
            organization_id=org.id,
        )
        db_session.add(member)
        await db_session.commit()
        await db_session.refresh(owner)

        response = await async_client.get(
            "/api/v1/dashboard/operational-costs?period=current_month",
            headers=get_auth_headers(owner),
        )
        assert response.status_code == 200
        data = response.json()
        assert float(data["resource_costs"]) >= 2500
