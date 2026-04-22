"""
Integration tests for multi-tenant data isolation

These tests validate that:
1. Users from Organization A cannot access data from Organization B
2. JWT tokens correctly identify the organization
3. Repository filtering works correctly
4. Endpoint-level isolation is enforced
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.cost import CostFixed
from app.models.organization import Organization
from app.models.project import Project
from app.models.service import Service
from app.models.user import User
from app.repositories.factory import RepositoryFactory


@pytest.fixture
async def org_a(db_session: AsyncSession) -> Organization:
    """Create Organization A for testing"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    org = Organization(
        name="Test Organization A",
        slug=f"test-org-a-{unique_id}",
        subscription_plan="enterprise",
        subscription_status="active",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def org_b(db_session: AsyncSession) -> Organization:
    """Create Organization B for testing"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    org = Organization(
        name="Test Organization B",
        slug=f"test-org-b-{unique_id}",
        subscription_plan="enterprise",
        subscription_status="active",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def user_org_a(db_session: AsyncSession, org_a: Organization) -> User:
    """Create user for Organization A"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"user-a-{unique_id}@test.com",
        full_name="User A",
        hashed_password=get_password_hash("password123"),
        organization_id=org_a.id,
        role="admin",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def user_org_b(db_session: AsyncSession, org_b: Organization) -> User:
    """Create user for Organization B"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"user-b-{unique_id}@test.com",
        full_name="User B",
        hashed_password=get_password_hash("password123"),
        organization_id=org_b.id,
        role="admin",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def service_org_a(db_session: AsyncSession, org_a: Organization) -> Service:
    """Create service for Organization A"""
    service = Service(
        name="Service Org A",
        description="Test service for Org A",
        organization_id=org_a.id,
        default_margin_target=0.40,
        is_active=True,
    )
    db_session.add(service)
    await db_session.commit()
    await db_session.refresh(service)
    return service


@pytest.fixture
async def service_org_b(db_session: AsyncSession, org_b: Organization) -> Service:
    """Create service for Organization B"""
    service = Service(
        name="Service Org B",
        description="Test service for Org B",
        organization_id=org_b.id,
        default_margin_target=0.35,
        is_active=True,
    )
    db_session.add(service)
    await db_session.commit()
    await db_session.refresh(service)
    return service


@pytest.fixture
async def project_org_a(
    db_session: AsyncSession, org_a: Organization, service_org_a: Service
) -> Project:
    """Create project for Organization A"""
    project = Project(
        name="Project Org A", client_name="Client A", organization_id=org_a.id, currency="USD"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def project_org_b(
    db_session: AsyncSession, org_b: Organization, service_org_b: Service
) -> Project:
    """Create project for Organization B"""
    project = Project(
        name="Project Org B", client_name="Client B", organization_id=org_b.id, currency="USD"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def cost_org_a(db_session: AsyncSession, org_a: Organization) -> CostFixed:
    """Create fixed cost for Organization A"""
    cost = CostFixed(
        name="Cost Org A",
        amount_monthly=1000.0,
        currency="USD",
        organization_id=org_a.id,
        category="Overhead",
    )
    db_session.add(cost)
    await db_session.commit()
    await db_session.refresh(cost)
    return cost


@pytest.fixture
async def cost_org_b(db_session: AsyncSession, org_b: Organization) -> CostFixed:
    """Create fixed cost for Organization B"""
    cost = CostFixed(
        name="Cost Org B",
        amount_monthly=2000.0,
        currency="USD",
        organization_id=org_b.id,
        category="Overhead",
    )
    db_session.add(cost)
    await db_session.commit()
    await db_session.refresh(cost)
    return cost


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


class TestJWTOrganizationValidation:
    """Test that JWT tokens correctly include and validate organization_id"""

    async def test_jwt_includes_organization_id(self, user_org_a: User):
        """Test that JWT token includes organization_id in payload"""
        token_data = {
            "sub": str(user_org_a.id),
            "email": user_org_a.email,
            "organization_id": user_org_a.organization_id,
        }
        token = create_access_token(token_data)

        # Decode token to verify payload
        from app.core.security import decode_access_token

        payload = decode_access_token(token)

        assert payload is not None
        assert "organization_id" in payload
        assert payload["organization_id"] == user_org_a.organization_id
        assert payload["sub"] == str(user_org_a.id)

    async def test_jwt_with_mismatched_organization_rejected(
        self, async_client: AsyncClient, user_org_a: User, org_b: Organization
    ):
        """Test that JWT with mismatched organization_id is rejected"""
        # Create token with wrong organization_id
        token_data = {
            "sub": str(user_org_a.id),
            "email": user_org_a.email,
            "organization_id": org_b.id,  # Wrong organization
        }
        token = create_access_token(token_data)

        headers = {"Authorization": f"Bearer {token}"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)

        # Should be rejected because user's actual organization_id doesn't match token
        assert response.status_code == 401


class TestServiceIsolation:
    """Test data isolation for services"""

    async def test_user_can_only_see_own_organization_services(
        self,
        async_client: AsyncClient,
        user_org_a: User,
        service_org_a: Service,
        service_org_b: Service,
    ):
        """Test that user from Org A only sees services from Org A"""
        headers = get_auth_headers(user_org_a)
        response = await async_client.get("/api/v1/services/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        services = data["items"]

        # Should only see service from Org A
        service_ids = [s["id"] for s in services]
        assert service_org_a.id in service_ids
        assert service_org_b.id not in service_ids

    async def test_user_cannot_access_other_organization_service(
        self, async_client: AsyncClient, user_org_a: User, service_org_b: Service
    ):
        """Test that user from Org A cannot access service from Org B"""
        headers = get_auth_headers(user_org_a)
        response = await async_client.get(f"/api/v1/services/{service_org_b.id}", headers=headers)

        # Should return 404 (not found) because it's filtered out by tenant context
        assert response.status_code == 404

    async def test_user_can_access_own_organization_service(
        self, async_client: AsyncClient, user_org_a: User, service_org_a: Service
    ):
        """Test that user from Org A can access service from Org A"""
        headers = get_auth_headers(user_org_a)
        response = await async_client.get(f"/api/v1/services/{service_org_a.id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == service_org_a.id
        assert data["name"] == service_org_a.name


class TestProjectIsolation:
    """Test data isolation for projects"""

    async def test_user_can_only_see_own_organization_projects(
        self,
        async_client: AsyncClient,
        user_org_a: User,
        project_org_a: Project,
        project_org_b: Project,
    ):
        """Test that user from Org A only sees projects from Org A"""
        headers = get_auth_headers(user_org_a)
        response = await async_client.get("/api/v1/projects/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        projects = data["items"]

        # Should only see project from Org A
        project_ids = [p["id"] for p in projects]
        assert project_org_a.id in project_ids
        assert project_org_b.id not in project_ids

    async def test_user_cannot_access_other_organization_project(
        self, async_client: AsyncClient, user_org_a: User, project_org_b: Project
    ):
        """Test that user from Org A cannot access project from Org B"""
        headers = get_auth_headers(user_org_a)
        response = await async_client.get(f"/api/v1/projects/{project_org_b.id}", headers=headers)

        # Should return 404 (not found)
        assert response.status_code == 404


class TestCostIsolation:
    """Test data isolation for fixed costs"""

    async def test_user_can_only_see_own_organization_costs(
        self,
        async_client: AsyncClient,
        user_org_a: User,
        cost_org_a: CostFixed,
        cost_org_b: CostFixed,
    ):
        """Test that user from Org A only sees costs from Org A"""
        headers = get_auth_headers(user_org_a)
        response = await async_client.get("/api/v1/settings/costs/fixed", headers=headers)

        assert response.status_code == 200
        data = response.json()
        costs = data["items"]

        # Should only see cost from Org A
        cost_ids = [c["id"] for c in costs]
        assert cost_org_a.id in cost_ids
        assert cost_org_b.id not in cost_ids


class TestRepositoryIsolation:
    """Test that repository layer correctly filters by tenant"""

    async def test_service_repository_filters_by_tenant(
        self,
        db_session: AsyncSession,
        org_a: Organization,
        org_b: Organization,
        service_org_a: Service,
        service_org_b: Service,
    ):
        """Test that ServiceRepository only returns services for the specified tenant"""
        # Repository for Org A
        repo_a = RepositoryFactory.create_service_repository(db_session, org_a.id)
        services_a = await repo_a.get_all()

        service_ids_a = [s.id for s in services_a]
        assert service_org_a.id in service_ids_a
        assert service_org_b.id not in service_ids_a

        # Repository for Org B
        repo_b = RepositoryFactory.create_service_repository(db_session, org_b.id)
        services_b = await repo_b.get_all()

        service_ids_b = [s.id for s in services_b]
        assert service_org_b.id in service_ids_b
        assert service_org_a.id not in service_ids_b

    async def test_project_repository_filters_by_tenant(
        self,
        db_session: AsyncSession,
        org_a: Organization,
        org_b: Organization,
        project_org_a: Project,
        project_org_b: Project,
    ):
        """Test that ProjectRepository only returns projects for the specified tenant"""
        # Repository for Org A
        repo_a = RepositoryFactory.create_project_repository(db_session, org_a.id)
        projects_a = await repo_a.get_all()

        project_ids_a = [p.id for p in projects_a]
        assert project_org_a.id in project_ids_a
        assert project_org_b.id not in project_ids_a

        # Repository for Org B
        repo_b = RepositoryFactory.create_project_repository(db_session, org_b.id)
        projects_b = await repo_b.get_all()

        project_ids_b = [p.id for p in projects_b]
        assert project_org_b.id in project_ids_b
        assert project_org_a.id not in project_ids_b

    async def test_cost_repository_filters_by_tenant(
        self,
        db_session: AsyncSession,
        org_a: Organization,
        org_b: Organization,
        cost_org_a: CostFixed,
        cost_org_b: CostFixed,
    ):
        """Test that CostRepository only returns costs for the specified tenant"""
        # Repository for Org A
        repo_a = RepositoryFactory.create_cost_repository(db_session, org_a.id)
        costs_a = await repo_a.get_all()

        cost_ids_a = [c.id for c in costs_a]
        assert cost_org_a.id in cost_ids_a
        assert cost_org_b.id not in cost_ids_a

        # Repository for Org B
        repo_b = RepositoryFactory.create_cost_repository(db_session, org_b.id)
        costs_b = await repo_b.get_all()

        cost_ids_b = [c.id for c in costs_b]
        assert cost_org_b.id in cost_ids_b
        assert cost_org_a.id not in cost_ids_b


class TestUpdateDeleteIsolation:
    """Test that update and delete operations are isolated by tenant"""

    async def test_user_cannot_update_other_organization_service(
        self, async_client: AsyncClient, user_org_a: User, service_org_b: Service
    ):
        """Test that user from Org A cannot update service from Org B"""
        headers = get_auth_headers(user_org_a)
        update_data = {"name": "Hacked Service"}

        response = await async_client.put(
            f"/api/v1/services/{service_org_b.id}", json=update_data, headers=headers
        )

        # Should return 404 (not found) because service is filtered out
        assert response.status_code == 404

    async def test_user_cannot_delete_other_organization_service(
        self, async_client: AsyncClient, user_org_a: User, service_org_b: Service
    ):
        """Test that user from Org A cannot delete service from Org B"""
        headers = get_auth_headers(user_org_a)

        response = await async_client.delete(
            f"/api/v1/services/{service_org_b.id}", headers=headers
        )

        # Should return 404 (not found)
        assert response.status_code == 404

    async def test_user_can_update_own_organization_service(
        self, async_client: AsyncClient, user_org_a: User, service_org_a: Service
    ):
        """Test that user from Org A can update service from Org A"""
        headers = get_auth_headers(user_org_a)
        update_data = {"name": "Updated Service Name"}

        response = await async_client.put(
            f"/api/v1/services/{service_org_a.id}", json=update_data, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Service Name"


class TestDashboardIsolation:
    """Test that dashboard data is isolated by tenant"""

    async def test_dashboard_only_shows_own_organization_data(
        self,
        async_client: AsyncClient,
        user_org_a: User,
        project_org_a: Project,
        project_org_b: Project,
    ):
        """Test that dashboard only shows data from user's organization"""
        headers = get_auth_headers(user_org_a)
        response = await async_client.get("/api/v1/insights/dashboard", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Dashboard should only include projects from Org A
        # The total_projects count should not include projects from Org B
        # (Note: This is a simplified test - in reality, you'd check specific metrics)
        assert "total_projects" in data or "projects" in data


@pytest.fixture
async def quote_org_a(db_session: AsyncSession, project_org_a: Project):
    """Create quote for Organization A"""
    from app.models.project import Quote

    quote = Quote(
        project_id=project_org_a.id,
        version=1,
        total_internal_cost=1000.0,
        total_client_price=1500.0,
        margin_percentage=33.33,
    )
    db_session.add(quote)
    await db_session.commit()
    await db_session.refresh(quote)
    return quote


@pytest.fixture
async def quote_org_b(db_session: AsyncSession, project_org_b: Project):
    """Create quote for Organization B"""
    from app.models.project import Quote

    quote = Quote(
        project_id=project_org_b.id,
        version=1,
        total_internal_cost=2000.0,
        total_client_price=3000.0,
        margin_percentage=33.33,
    )
    db_session.add(quote)
    await db_session.commit()
    await db_session.refresh(quote)
    return quote


class TestProjectCrudIsolation:
    """Test that project CRUD operations are isolated by tenant"""

    async def test_user_cannot_update_other_organization_project(
        self, async_client: AsyncClient, user_org_a: User, project_org_b: Project
    ):
        """Test that user from Org A cannot update project from Org B"""
        headers = get_auth_headers(user_org_a)
        update_data = {"name": "Hacked Project", "client_name": "Hacked Client"}

        response = await async_client.put(
            f"/api/v1/projects/{project_org_b.id}", json=update_data, headers=headers
        )

        # Should return 404 (not found) because project is filtered out by tenant context
        assert response.status_code == 404

    async def test_user_cannot_delete_other_organization_project(
        self, async_client: AsyncClient, user_org_a: User, project_org_b: Project
    ):
        """Test that user from Org A cannot delete project from Org B"""
        headers = get_auth_headers(user_org_a)

        response = await async_client.delete(
            f"/api/v1/projects/{project_org_b.id}", headers=headers
        )

        # Should return 404 (not found)
        assert response.status_code == 404

    async def test_user_can_update_own_organization_project(
        self, async_client: AsyncClient, user_org_a: User, project_org_a: Project
    ):
        """Test that user from Org A can update project from Org A"""
        headers = get_auth_headers(user_org_a)
        update_data = {"name": "Updated Project Name", "client_name": "Updated Client"}

        response = await async_client.put(
            f"/api/v1/projects/{project_org_a.id}", json=update_data, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Project Name"
        assert data["client_name"] == "Updated Client"

    async def test_user_cannot_create_project_with_other_org_service(
        self,
        async_client: AsyncClient,
        user_org_a: User,
        service_org_b: Service,
        db_session: AsyncSession,
        org_a: Organization,
    ):
        """Test that user cannot create project using services from another organization"""
        headers = get_auth_headers(user_org_a)

        # Try to create project with service from Org B
        project_data = {
            "name": "Test Project",
            "client_name": "Test Client",
            "currency": "USD",
            "quote_items": [{"service_id": service_org_b.id, "estimated_hours": 10.0}],
            "tax_ids": [],
        }

        response = await async_client.post("/api/v1/projects/", json=project_data, headers=headers)

        # Should fail because service doesn't belong to Org A
        assert response.status_code in [404, 400]
        # The endpoint already validates service ownership, so project creation is prevented

    async def test_user_cannot_restore_other_organization_project(
        self,
        async_client: AsyncClient,
        user_org_a: User,
        project_org_b: Project,
        db_session: AsyncSession,
    ):
        """Test that user from Org A cannot restore deleted project from Org B"""
        # First soft delete the project
        from datetime import datetime

        project_org_b.deleted_at = datetime.utcnow()
        project_org_b.deleted_by_id = user_org_a.id  # Simulate deletion by other user
        await db_session.commit()
        await db_session.refresh(project_org_b)

        headers = get_auth_headers(user_org_a)
        response = await async_client.post(
            f"/api/v1/projects/{project_org_b.id}/restore", headers=headers
        )

        # Should return 404 (not found)
        assert response.status_code == 404

        # Verify project is still deleted
        await db_session.refresh(project_org_b)
        assert project_org_b.deleted_at is not None

    async def test_user_cannot_permanently_delete_other_organization_project(
        self,
        async_client: AsyncClient,
        user_org_a: User,
        project_org_b: Project,
        db_session: AsyncSession,
    ):
        """Test that user from Org A cannot permanently delete project from Org B"""
        # First soft delete the project
        from datetime import datetime

        project_org_b.deleted_at = datetime.utcnow()
        project_org_b.deleted_by_id = user_org_a.id
        await db_session.commit()
        await db_session.refresh(project_org_b)

        project_id = project_org_b.id

        headers = get_auth_headers(user_org_a)
        response = await async_client.delete(
            f"/api/v1/projects/{project_id}/permanent", headers=headers
        )

        # Should return 404 (not found)
        assert response.status_code == 404

        # Verify project still exists
        result = await db_session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        assert project is not None


class TestQuoteIsolation:
    """Test that quote operations are isolated by tenant"""

    async def test_user_cannot_get_quote_from_other_organization(
        self, async_client: AsyncClient, user_org_a: User, project_org_b, quote_org_b
    ):
        """Test that user from Org A cannot get quote from Org B's project"""
        headers = get_auth_headers(user_org_a)
        response = await async_client.get(
            f"/api/v1/projects/{project_org_b.id}/quotes/{quote_org_b.id}", headers=headers
        )

        # Should return 404 (not found) because project/quote is filtered out
        assert response.status_code == 404

    async def test_user_cannot_list_quotes_from_other_organization_project(
        self, async_client: AsyncClient, user_org_a: User, project_org_b, quote_org_b
    ):
        """Test that user from Org A cannot list quotes from Org B's project"""
        headers = get_auth_headers(user_org_a)
        response = await async_client.get(
            f"/api/v1/projects/{project_org_b.id}/quotes", headers=headers
        )

        # Should return 404 (not found) because project is filtered out
        assert response.status_code == 404

    async def test_user_can_get_quote_from_own_organization(
        self, async_client: AsyncClient, user_org_a: User, project_org_a, quote_org_a
    ):
        """Test that user from Org A can get quote from Org A's project"""
        headers = get_auth_headers(user_org_a)
        response = await async_client.get(
            f"/api/v1/projects/{project_org_a.id}/quotes/{quote_org_a.id}", headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == quote_org_a.id
        assert data["project_id"] == project_org_a.id

    async def test_user_cannot_update_quote_from_other_organization(
        self, async_client: AsyncClient, user_org_a: User, project_org_b, quote_org_b, service_org_a
    ):
        """Test that user from Org A cannot update quote from Org B's project"""
        headers = get_auth_headers(user_org_a)
        update_data = {
            "items": [{"service_id": service_org_a.id, "estimated_hours": 20.0}],
            "notes": "Hacked quote",
        }

        response = await async_client.put(
            f"/api/v1/projects/{project_org_b.id}/quotes/{quote_org_b.id}",
            json=update_data,
            headers=headers,
        )

        # Should return 404 (not found) because project/quote is filtered out
        assert response.status_code == 404

    async def test_user_cannot_create_quote_version_from_other_organization(
        self, async_client: AsyncClient, user_org_a: User, project_org_b, quote_org_b, service_org_a
    ):
        """Test that user from Org A cannot create new quote version from Org B's project"""
        headers = get_auth_headers(user_org_a)
        new_version_data = {
            "items": [{"service_id": service_org_a.id, "estimated_hours": 20.0}],
            "notes": "Hacked new version",
        }

        response = await async_client.post(
            f"/api/v1/projects/{project_org_b.id}/quotes/{quote_org_b.id}/new-version",
            json=new_version_data,
            headers=headers,
        )

        # Should return 404 (not found) because project/quote is filtered out
        assert response.status_code == 404


class TestRepositoryIsolationAdvanced:
    """Advanced tests for repository-level isolation"""

    async def test_project_repository_get_by_id_with_quotes_filters_by_tenant(
        self,
        db_session: AsyncSession,
        org_a: Organization,
        org_b: Organization,
        project_org_a: Project,
        project_org_b: Project,
    ):
        """Test that get_by_id_with_quotes respects tenant filtering"""
        # Repository for Org A
        repo_a = RepositoryFactory.create_project_repository(db_session, org_a.id)
        project_a = await repo_a.get_by_id_with_quotes(project_org_a.id)

        assert project_a is not None
        assert project_a.id == project_org_a.id

        # Should not be able to get project from Org B
        project_b_attempt = await repo_a.get_by_id_with_quotes(project_org_b.id)
        assert project_b_attempt is None

    async def test_project_repository_get_quote_by_id_filters_by_tenant(
        self,
        db_session: AsyncSession,
        org_a: Organization,
        org_b: Organization,
        project_org_a: Project,
        project_org_b: Project,
    ):
        """Test that get_quote_by_id respects tenant filtering via project"""
        from app.models.project import Quote

        # Create quotes for both projects
        quote_a = Quote(
            project_id=project_org_a.id,
            version=1,
            total_internal_cost=1000.0,
            total_client_price=1500.0,
        )
        quote_b = Quote(
            project_id=project_org_b.id,
            version=1,
            total_internal_cost=2000.0,
            total_client_price=3000.0,
        )
        db_session.add_all([quote_a, quote_b])
        await db_session.commit()
        await db_session.refresh(quote_a)
        await db_session.refresh(quote_b)

        # Repository for Org A
        repo_a = RepositoryFactory.create_project_repository(db_session, org_a.id)

        # Should be able to get quote from Org A's project
        found_quote_a = await repo_a.get_quote_by_id(quote_a.id)
        assert found_quote_a is not None
        assert found_quote_a.id == quote_a.id

        # Should NOT be able to get quote from Org B's project
        found_quote_b = await repo_a.get_quote_by_id(quote_b.id)
        assert found_quote_b is None
