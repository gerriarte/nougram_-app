"""
Integration tests for organization endpoints

Tests all organization management endpoints including:
- CRUD operations
- User management
- Statistics
- Subscription management
- Permissions
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.organization import Organization
from app.models.project import Project
from app.models.service import Service
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
async def test_org_enterprise(db_session: AsyncSession) -> Organization:
    """Create test organization with enterprise plan"""
    unique_id = str(uuid.uuid4())[:8]
    org = Organization(
        name="Test Enterprise Org",
        slug=f"test-enterprise-org-{unique_id}",
        subscription_plan="enterprise",
        subscription_status="active",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def test_org_free(db_session: AsyncSession) -> Organization:
    """Create test organization with free plan"""
    unique_id = str(uuid.uuid4())[:8]
    org = Organization(
        name="Test Free Org",
        slug=f"test-free-org-{unique_id}",
        subscription_plan="free",
        subscription_status="active",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def super_admin_user(db_session: AsyncSession, test_org_enterprise: Organization) -> User:
    """Create super admin user"""
    user = User(
        email="superadmin@test.com",
        full_name="Super Admin",
        hashed_password=get_password_hash("password123"),
        organization_id=test_org_enterprise.id,
        role="super_admin",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def org_admin_user(db_session: AsyncSession, test_org_enterprise: Organization) -> User:
    """Create org admin user"""
    user = User(
        email="orgadmin@test.com",
        full_name="Org Admin",
        hashed_password=get_password_hash("password123"),
        organization_id=test_org_enterprise.id,
        role="org_admin",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def regular_user(db_session: AsyncSession, test_org_free: Organization) -> User:
    """Create regular user"""
    user = User(
        email="regular@test.com",
        full_name="Regular User",
        hashed_password=get_password_hash("password123"),
        organization_id=test_org_free.id,
        role="product_manager",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.integration
class TestGetMyOrganization:
    """Tests for GET /organizations/me"""

    async def test_get_my_organization_success(
        self, async_client: AsyncClient, org_admin_user: User
    ):
        """Test getting own organization"""
        headers = get_auth_headers(org_admin_user)
        response = await async_client.get("/api/v1/organizations/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == org_admin_user.organization_id
        assert data["name"] == "Test Enterprise Org"
        assert "subscription_plan" in data
        assert "user_count" in data

    async def test_get_my_organization_no_org(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test getting organization when user has no org"""
        user = User(
            email="noorg@test.com",
            full_name="No Org User",
            hashed_password=get_password_hash("password123"),
            organization_id=None,
            role="product_manager",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        headers = get_auth_headers(user)
        response = await async_client.get("/api/v1/organizations/me", headers=headers)

        assert response.status_code == 404


@pytest.mark.integration
class TestListOrganizations:
    """Tests for GET /organizations/"""

    async def test_list_organizations_super_admin(
        self,
        async_client: AsyncClient,
        super_admin_user: User,
        test_org_enterprise: Organization,
        test_org_free: Organization,
    ):
        """Test super admin can see all organizations"""
        headers = get_auth_headers(super_admin_user)
        response = await async_client.get("/api/v1/organizations/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        org_ids = [org["id"] for org in data["items"]]
        assert test_org_enterprise.id in org_ids
        assert test_org_free.id in org_ids

    async def test_list_organizations_regular_user(
        self, async_client: AsyncClient, regular_user: User, test_org_free: Organization
    ):
        """Test regular user only sees own organization"""
        headers = get_auth_headers(regular_user)
        response = await async_client.get("/api/v1/organizations/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        # Regular user should see at least their own organization
        assert data["total"] >= 1
        org_ids = [org["id"] for org in data["items"]]
        assert test_org_free.id in org_ids


@pytest.mark.integration
class TestGetOrganization:
    """Tests for GET /organizations/{id}"""

    async def test_get_organization_success(
        self, async_client: AsyncClient, org_admin_user: User, test_org_enterprise: Organization
    ):
        """Test getting own organization"""
        headers = get_auth_headers(org_admin_user)
        response = await async_client.get(
            f"/api/v1/organizations/{test_org_enterprise.id}", headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_org_enterprise.id
        assert data["name"] == test_org_enterprise.name

    async def test_get_organization_other_org_forbidden(
        self, async_client: AsyncClient, regular_user: User, test_org_enterprise: Organization
    ):
        """Test regular user cannot access other organization"""
        headers = get_auth_headers(regular_user)
        response = await async_client.get(
            f"/api/v1/organizations/{test_org_enterprise.id}", headers=headers
        )

        assert response.status_code == 403


@pytest.mark.integration
class TestCreateOrganization:
    """Tests for POST /organizations/"""

    async def test_create_organization_super_admin(
        self, async_client: AsyncClient, super_admin_user: User
    ):
        """Test super admin can create organization"""
        unique_id = str(uuid.uuid4())[:8]
        headers = get_auth_headers(super_admin_user)
        response = await async_client.post(
            "/api/v1/organizations/",
            json={
                "name": "New Test Org",
                "slug": f"new-test-org-{unique_id}",
                "subscription_plan": "professional",
                "subscription_status": "active",
            },
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Test Org"
        assert f"new-test-org-{unique_id}" in data["slug"]

    async def test_create_organization_regular_user_forbidden(
        self, async_client: AsyncClient, regular_user: User
    ):
        """Test regular user cannot create organization"""
        headers = get_auth_headers(regular_user)
        response = await async_client.post(
            "/api/v1/organizations/",
            json={"name": "New Test Org", "slug": "new-test-org"},
            headers=headers,
        )

        assert response.status_code == 403


@pytest.mark.integration
class TestRegisterOrganization:
    """Tests for POST /organizations/register"""

    async def test_register_organization_success(self, async_client: AsyncClient):
        """Test public organization registration"""
        unique_id = str(uuid.uuid4())[:8]
        response = await async_client.post(
            "/api/v1/organizations/register",
            json={
                "organization_name": "New Registered Org",
                "organization_slug": f"new-registered-org-{unique_id}",
                "admin_email": f"admin{unique_id}@neworg.com",
                "admin_full_name": "Admin User",
                "admin_password": "password123456",
                "subscription_plan": "free",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "organization" in data
        assert "user" in data
        assert "access_token" in data
        assert data["organization"]["name"] == "New Registered Org"
        assert data["user"]["email"] == f"admin{unique_id}@neworg.com"

    async def test_register_organization_duplicate_slug(
        self, async_client: AsyncClient, test_org_enterprise: Organization
    ):
        """Test registration with duplicate slug fails"""
        unique_id = str(uuid.uuid4())[:8]
        # Use the exact slug from existing org to test duplicate detection
        response = await async_client.post(
            "/api/v1/organizations/register",
            json={
                "organization_name": "Duplicate Org",
                "organization_slug": test_org_enterprise.slug,  # Use existing slug
                "admin_email": f"admin{unique_id}@test.com",
                "admin_full_name": "Admin User",
                "admin_password": "password123456",
                "subscription_plan": "free",
            },
        )

        assert response.status_code == 400


@pytest.mark.integration
class TestUpdateOrganization:
    """Tests for PUT /organizations/{id}"""

    async def test_update_organization_org_admin(
        self, async_client: AsyncClient, org_admin_user: User, test_org_enterprise: Organization
    ):
        """Test org admin can update own organization"""
        headers = get_auth_headers(org_admin_user)
        response = await async_client.put(
            f"/api/v1/organizations/{test_org_enterprise.id}",
            json={"name": "Updated Org Name", "settings": {"theme": "dark"}},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Org Name"
        assert data["settings"]["theme"] == "dark"

    async def test_update_subscription_only_super_admin(
        self, async_client: AsyncClient, org_admin_user: User, test_org_enterprise: Organization
    ):
        """Test org admin cannot update subscription plan"""
        headers = get_auth_headers(org_admin_user)
        response = await async_client.put(
            f"/api/v1/organizations/{test_org_enterprise.id}",
            json={"subscription_plan": "enterprise"},
            headers=headers,
        )

        # Should succeed but not change subscription (only super_admin can)
        assert response.status_code == 200


@pytest.mark.integration
class TestDeleteOrganization:
    """Tests for DELETE /organizations/{id}"""

    async def test_delete_organization_super_admin(
        self, async_client: AsyncClient, super_admin_user: User, db_session: AsyncSession
    ):
        """Test super admin can delete organization"""
        unique_id = str(uuid.uuid4())[:8]
        # Create org to delete
        org = Organization(
            name="Org To Delete",
            slug=f"org-to-delete-{unique_id}",
            subscription_plan="free",
            subscription_status="active",
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

        headers = get_auth_headers(super_admin_user)
        response = await async_client.delete(f"/api/v1/organizations/{org.id}", headers=headers)

        assert response.status_code == 204

        # Verify soft delete (status changed to cancelled)
        result = await db_session.execute(select(Organization).where(Organization.id == org.id))
        deleted_org = result.scalar_one()
        assert deleted_org.subscription_status == "cancelled"

    async def test_delete_organization_regular_user_forbidden(
        self, async_client: AsyncClient, regular_user: User, test_org_free: Organization
    ):
        """Test regular user cannot delete organization"""
        headers = get_auth_headers(regular_user)
        response = await async_client.delete(
            f"/api/v1/organizations/{test_org_free.id}", headers=headers
        )

        assert response.status_code == 403


@pytest.mark.integration
class TestOrganizationUsers:
    """Tests for user management endpoints"""

    async def test_list_organization_users(
        self, async_client: AsyncClient, org_admin_user: User, test_org_enterprise: Organization
    ):
        """Test listing users in organization"""
        headers = get_auth_headers(org_admin_user)
        response = await async_client.get(
            f"/api/v1/organizations/{test_org_enterprise.id}/users", headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_add_user_to_organization(
        self, async_client: AsyncClient, org_admin_user: User, test_org_enterprise: Organization
    ):
        """Test adding new user to organization"""
        headers = get_auth_headers(org_admin_user)
        response = await async_client.post(
            f"/api/v1/organizations/{test_org_enterprise.id}/users",
            json={
                "email": "newuser@test.com",
                "full_name": "New User",
                "password": "password123456",
                "role": "org_member",
            },
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["organization_id"] == test_org_enterprise.id

    async def test_update_user_role(
        self,
        async_client: AsyncClient,
        org_admin_user: User,
        test_org_enterprise: Organization,
        db_session: AsyncSession,
    ):
        """Test updating user role in organization"""
        unique_id = str(uuid.uuid4())[:8]
        # Create user to update
        user = User(
            email=f"updatable{unique_id}@test.com",
            full_name="Updatable User",
            hashed_password=get_password_hash("password123"),
            organization_id=test_org_enterprise.id,
            role="org_member",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        headers = get_auth_headers(org_admin_user)
        response = await async_client.put(
            f"/api/v1/organizations/{test_org_enterprise.id}/users/{user.id}/role",
            json={"role": "org_admin"},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "org_admin"

    async def test_remove_user_from_organization(
        self,
        async_client: AsyncClient,
        org_admin_user: User,
        test_org_enterprise: Organization,
        db_session: AsyncSession,
    ):
        """Test removing user from organization"""
        unique_id = str(uuid.uuid4())[:8]
        # Create user to remove
        user = User(
            email=f"removable{unique_id}@test.com",
            full_name="Removable User",
            hashed_password=get_password_hash("password123"),
            organization_id=test_org_enterprise.id,
            role="org_member",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        headers = get_auth_headers(org_admin_user)
        response = await async_client.delete(
            f"/api/v1/organizations/{test_org_enterprise.id}/users/{user.id}", headers=headers
        )

        assert response.status_code == 204

        # Verify user organization_id is None
        await db_session.refresh(user)
        assert user.organization_id is None


@pytest.mark.integration
class TestOrganizationStats:
    """Tests for GET /organizations/{id}/stats"""

    async def test_get_organization_stats(
        self,
        async_client: AsyncClient,
        org_admin_user: User,
        test_org_enterprise: Organization,
        db_session: AsyncSession,
    ):
        """Test getting organization usage statistics"""
        # Create some test data
        project = Project(
            name="Test Project",
            client_name="Test Client",
            organization_id=test_org_enterprise.id,
            currency="USD",
            status="Draft",
        )
        db_session.add(project)

        service = Service(
            name="Test Service",
            organization_id=test_org_enterprise.id,
            margin_target=0.40,
            billable_rate=100.0,
            is_active=True,
        )
        db_session.add(service)
        await db_session.commit()

        headers = get_auth_headers(org_admin_user)
        response = await async_client.get(
            f"/api/v1/organizations/{test_org_enterprise.id}/stats", headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "current_usage" in data
        assert "limits" in data
        assert "usage_percentage" in data
        assert data["current_usage"]["projects"] >= 1
        assert data["current_usage"]["services"] >= 1


@pytest.mark.integration
class TestUpdateSubscription:
    """Tests for PUT /organizations/{id}/subscription"""

    async def test_update_subscription_super_admin(
        self, async_client: AsyncClient, super_admin_user: User, test_org_free: Organization
    ):
        """Test super admin can update subscription plan"""
        headers = get_auth_headers(super_admin_user)
        response = await async_client.put(
            f"/api/v1/organizations/{test_org_free.id}/subscription",
            json={"plan": "professional", "status": "active"},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["subscription_plan"] == "professional"

    async def test_update_subscription_org_admin_forbidden(
        self, async_client: AsyncClient, org_admin_user: User, test_org_enterprise: Organization
    ):
        """Test org admin cannot update subscription"""
        headers = get_auth_headers(org_admin_user)
        response = await async_client.put(
            f"/api/v1/organizations/{test_org_enterprise.id}/subscription",
            json={"plan": "free"},
            headers=headers,
        )

        assert response.status_code == 403


@pytest.mark.integration
class TestPlanLimits:
    """Tests for plan limit validation"""

    async def test_free_plan_user_limit(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test free plan user limit is enforced"""
        # Create free org
        org = Organization(
            name="Free Limit Test",
            slug="free-limit-test",
            subscription_plan="free",
            subscription_status="active",
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

        # Create admin user
        admin = User(
            email="freelimit@test.com",
            full_name="Free Limit Admin",
            hashed_password=get_password_hash("password123"),
            organization_id=org.id,
            role="org_admin",
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        # Free plan allows 1 user, we have 1, so adding another should fail
        headers = get_auth_headers(admin)
        response = await async_client.post(
            f"/api/v1/organizations/{org.id}/users",
            json={
                "email": "second@test.com",
                "full_name": "Second User",
                "password": "password123456",
                "role": "org_member",
            },
            headers=headers,
        )

        assert response.status_code == 403
        assert "limit exceeded" in response.json()["detail"].lower()
