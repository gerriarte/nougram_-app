"""
Advanced security tests for multi-tenant architecture

Tests for:
1. Data leakage prevention
2. Cross-tenant access prevention (comprehensive)
3. Plan limit validation
4. Edge cases and security vulnerabilities
"""

from datetime import UTC

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plan_limits import get_plan_limit
from app.core.security import create_access_token, get_password_hash
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
        subscription_plan="free",
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
        subscription_plan="starter",
        subscription_status="active",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def user_org_a(db_session: AsyncSession, org_a: Organization) -> User:
    """Create user for Organization A"""
    user = User(
        email=f"user_a@{org_a.slug}.test",
        full_name="User A",
        hashed_password=get_password_hash("password123"),
        organization_id=org_a.id,
        role="owner",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def user_org_b(db_session: AsyncSession, org_b: Organization) -> User:
    """Create user for Organization B"""
    user = User(
        email=f"user_b@{org_b.slug}.test",
        full_name="User B",
        hashed_password=get_password_hash("password123"),
        organization_id=org_b.id,
        role="owner",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def project_org_a(db_session: AsyncSession, org_a: Organization) -> Project:
    """Create project for Organization A"""
    project = Project(name="Project A", client_name="Client A", organization_id=org_a.id)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def project_org_b(db_session: AsyncSession, org_b: Organization) -> Project:
    """Create project for Organization B"""
    project = Project(name="Project B", client_name="Client B", organization_id=org_b.id)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def service_org_a(db_session: AsyncSession, org_a: Organization) -> Service:
    """Create service for Organization A"""
    service = Service(
        name="Service A",
        description="Service from Org A",
        organization_id=org_a.id,
        default_margin_target=0.30,
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
        name="Service B",
        description="Service from Org B",
        organization_id=org_b.id,
        default_margin_target=0.30,
        is_active=True,
    )
    db_session.add(service)
    await db_session.commit()
    await db_session.refresh(service)
    return service


@pytest.mark.integration
class TestDataLeakagePrevention:
    """Tests to prevent data leakage between tenants"""

    async def test_user_cannot_list_other_tenant_projects(
        self,
        async_client: AsyncClient,
        user_org_a: User,
        project_org_a: Project,
        project_org_b: Project,
    ):
        """Test that listing projects only returns projects from user's organization"""
        token = create_access_token(
            {
                "sub": str(user_org_a.id),
                "email": user_org_a.email,
                "name": user_org_a.full_name,
                "organization_id": user_org_a.organization_id,
                "role": user_org_a.role,
                "role_type": "tenant",
            }
        )

        response = await async_client.get(
            "/api/v1/projects/", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        project_ids = [p["id"] for p in data.get("items", [])]

        # Should include own project
        assert project_org_a.id in project_ids
        # Should NOT include other tenant's project
        assert project_org_b.id not in project_ids

    async def test_user_cannot_list_other_tenant_services(
        self,
        async_client: AsyncClient,
        user_org_a: User,
        service_org_a: Service,
        service_org_b: Service,
    ):
        """Test that listing services only returns services from user's organization"""
        token = create_access_token(
            {
                "sub": str(user_org_a.id),
                "email": user_org_a.email,
                "name": user_org_a.full_name,
                "organization_id": user_org_a.organization_id,
                "role": user_org_a.role,
                "role_type": "tenant",
            }
        )

        response = await async_client.get(
            "/api/v1/services/", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        service_ids = [s["id"] for s in data.get("items", [])]

        # Should include own service
        assert service_org_a.id in service_ids
        # Should NOT include other tenant's service
        assert service_org_b.id not in service_ids

    async def test_user_cannot_access_other_tenant_project_by_id(
        self, async_client: AsyncClient, user_org_a: User, project_org_b: Project
    ):
        """Test that accessing project by ID from another tenant returns 404"""
        token = create_access_token(
            {
                "sub": str(user_org_a.id),
                "email": user_org_a.email,
                "name": user_org_a.full_name,
                "organization_id": user_org_a.organization_id,
                "role": user_org_a.role,
                "role_type": "tenant",
            }
        )

        response = await async_client.get(
            f"/api/v1/projects/{project_org_b.id}", headers={"Authorization": f"Bearer {token}"}
        )

        # Should return 404 (not found) or 403 (forbidden)
        assert response.status_code in [404, 403]

    async def test_user_cannot_modify_other_tenant_project(
        self, async_client: AsyncClient, user_org_a: User, project_org_b: Project
    ):
        """Test that modifying project from another tenant is prevented"""
        token = create_access_token(
            {
                "sub": str(user_org_a.id),
                "email": user_org_a.email,
                "name": user_org_a.full_name,
                "organization_id": user_org_a.organization_id,
                "role": user_org_a.role,
                "role_type": "tenant",
            }
        )

        response = await async_client.put(
            f"/api/v1/projects/{project_org_b.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Hacked Project", "client_name": "Hacked Client"},
        )

        # Should return 404 (not found) or 403 (forbidden)
        assert response.status_code in [404, 403]

    async def test_user_cannot_delete_other_tenant_project(
        self, async_client: AsyncClient, user_org_a: User, project_org_b: Project
    ):
        """Test that deleting project from another tenant is prevented"""
        token = create_access_token(
            {
                "sub": str(user_org_a.id),
                "email": user_org_a.email,
                "name": user_org_a.full_name,
                "organization_id": user_org_a.organization_id,
                "role": user_org_a.role,
                "role_type": "tenant",
            }
        )

        response = await async_client.delete(
            f"/api/v1/projects/{project_org_b.id}", headers={"Authorization": f"Bearer {token}"}
        )

        # Should return 404 (not found) or 403 (forbidden)
        assert response.status_code in [404, 403]


@pytest.mark.integration
class TestCrossTenantAccessPrevention:
    """Comprehensive tests for cross-tenant access prevention"""

    async def test_token_with_wrong_organization_id_blocked(
        self,
        async_client: AsyncClient,
        user_org_a: User,
        org_b: Organization,
        project_org_a: Project,
    ):
        """Test that token with wrong organization_id cannot access data"""
        # Create token with wrong organization_id
        token = create_access_token(
            {
                "sub": str(user_org_a.id),
                "email": user_org_a.email,
                "name": user_org_a.full_name,
                "organization_id": org_b.id,  # Wrong org ID
                "role": user_org_a.role,
                "role_type": "tenant",
            }
        )

        # Try to access own project with wrong org token
        response = await async_client.get(
            f"/api/v1/projects/{project_org_a.id}", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code in [404, 403, 401]

    async def test_repository_isolation_enforced(
        self,
        db_session: AsyncSession,
        org_a: Organization,
        org_b: Organization,
        project_org_a: Project,
        project_org_b: Project,
    ):
        """Test that repositories enforce tenant isolation"""
        # Repository for Org A should only return Org A projects
        repo_a = RepositoryFactory.create_project_repository(db_session, org_a.id)
        projects_a = await repo_a.get_all()
        project_ids_a = [p.id for p in projects_a]

        assert project_org_a.id in project_ids_a
        assert project_org_b.id not in project_ids_a

        # Repository for Org B should only return Org B projects
        repo_b = RepositoryFactory.create_project_repository(db_session, org_b.id)
        projects_b = await repo_b.get_all()
        project_ids_b = [p.id for p in projects_b]

        assert project_org_b.id in project_ids_b
        assert project_org_a.id not in project_ids_b

    async def test_direct_database_query_requires_organization_filter(
        self,
        db_session: AsyncSession,
        org_a: Organization,
        org_b: Organization,
        project_org_a: Project,
        project_org_b: Project,
    ):
        """Test that direct database queries without organization filter are dangerous"""
        # This test documents that we should ALWAYS filter by organization_id
        # Query WITHOUT filter (bad practice - but showing what NOT to do)
        result_unfiltered = await db_session.execute(select(Project))
        all_projects = result_unfiltered.scalars().all()
        all_ids = [p.id for p in all_projects]

        # This would return projects from both orgs (BAD!)
        # In production, repositories should NEVER do this
        assert project_org_a.id in all_ids
        assert project_org_b.id in all_ids

        # Query WITH filter (correct practice)
        result_filtered = await db_session.execute(
            select(Project).where(Project.organization_id == org_a.id)
        )
        filtered_projects = result_filtered.scalars().all()
        filtered_ids = [p.id for p in filtered_projects]

        # This correctly returns only Org A projects
        assert project_org_a.id in filtered_ids
        assert project_org_b.id not in filtered_ids


@pytest.mark.integration
class TestPlanLimitValidation:
    """Tests for plan limit validation"""

    async def test_free_plan_project_limit_enforced(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        org_a: Organization,
        user_org_a: User,
    ):
        """Test that free plan cannot exceed project limit"""
        # Free plan limit is 5 projects
        limit = get_plan_limit("free", "max_projects")
        assert limit == 5

        # Create projects up to the limit
        for i in range(limit):
            project = Project(
                name=f"Project {i}", client_name=f"Client {i}", organization_id=org_a.id
            )
            db_session.add(project)
        await db_session.commit()

        # Verify we're at the limit
        result = await db_session.execute(
            select(func.count(Project.id)).where(
                Project.organization_id == org_a.id, Project.deleted_at.is_(None)
            )
        )
        current_count = result.scalar() or 0
        assert current_count == limit

        seed_svc = Service(
            name="Seed Project Service",
            description="For API project create",
            organization_id=org_a.id,
            default_margin_target=0.30,
            is_active=True,
        )
        db_session.add(seed_svc)
        await db_session.commit()
        await db_session.refresh(seed_svc)

        # Now try to create one more (should fail)
        token = create_access_token(
            {
                "sub": str(user_org_a.id),
                "email": user_org_a.email,
                "name": user_org_a.full_name,
                "organization_id": user_org_a.organization_id,
                "role": user_org_a.role,
                "role_type": "tenant",
            }
        )

        response = await async_client.post(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Exceeding Project",
                "client_name": "Exceeding Client",
                "quote_items": [{"service_id": seed_svc.id, "estimated_hours": 1.0}],
            },
        )

        # Should return 403 Forbidden
        assert response.status_code == 403
        assert "limit exceeded" in response.json()["detail"].lower()

    async def test_enterprise_plan_unlimited_projects(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        org_b: Organization,
        user_org_b: User,
    ):
        """Test that enterprise plan has unlimited projects"""
        # Change org to enterprise plan
        org_b.subscription_plan = "enterprise"
        await db_session.commit()

        # Enterprise plan limit is -1 (unlimited)
        limit = get_plan_limit("enterprise", "max_projects")
        assert limit == -1

        seed_svc = Service(
            name="Seed Project Service Enterprise",
            description="For API project create",
            organization_id=org_b.id,
            default_margin_target=0.30,
            is_active=True,
        )
        db_session.add(seed_svc)
        await db_session.commit()
        await db_session.refresh(seed_svc)

        # Create many projects (should not hit limit)
        token = create_access_token(
            {
                "sub": str(user_org_b.id),
                "email": user_org_b.email,
                "name": user_org_b.full_name,
                "organization_id": user_org_b.organization_id,
                "role": user_org_b.role,
                "role_type": "tenant",
            }
        )

        # Create 10 projects (more than free/starter limits)
        for i in range(10):
            response = await async_client.post(
                "/api/v1/projects/",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": f"Enterprise Project {i}",
                    "client_name": f"Client {i}",
                    "quote_items": [{"service_id": seed_svc.id, "estimated_hours": 1.0}],
                },
            )
            # Should succeed (no limit)
            assert response.status_code == 201

    async def test_service_limit_enforced(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        org_a: Organization,
        user_org_a: User,
    ):
        """Test that service limit is enforced"""
        # Free plan limit is 10 services
        limit = get_plan_limit("free", "max_services")
        assert limit == 10

        # Create services up to the limit
        for i in range(limit):
            service = Service(
                name=f"Service {i}",
                description=f"Service {i} description",
                organization_id=org_a.id,
                default_margin_target=0.30,
                is_active=True,
            )
            db_session.add(service)
        await db_session.commit()

        # Try to create one more (should fail)
        token = create_access_token(
            {
                "sub": str(user_org_a.id),
                "email": user_org_a.email,
                "name": user_org_a.full_name,
                "organization_id": user_org_a.organization_id,
                "role": user_org_a.role,
                "role_type": "tenant",
            }
        )

        response = await async_client.post(
            "/api/v1/services/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Exceeding Service",
                "description": "This should fail",
                "default_margin_target": 0.30,
            },
        )

        # Should return 403 Forbidden
        assert response.status_code == 403
        assert "limit exceeded" in response.json()["detail"].lower()


@pytest.mark.integration
class TestSecurityEdgeCases:
    """Tests for edge cases and potential security vulnerabilities"""

    async def test_user_with_null_organization_id_blocked(
        self, async_client: AsyncClient, db_session: AsyncSession, org_a: Organization
    ):
        """Test that user with null organization_id cannot access endpoints"""
        # Create user without organization_id
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

        # Try to create token (might work, but access should fail)
        token = create_access_token(
            {
                "sub": str(user.id),
                "email": user.email,
                "name": user.full_name,
                "organization_id": None,
                "role": user.role,
                "role_type": "tenant",
            }
        )

        # Try to access projects endpoint
        response = await async_client.get(
            "/api/v1/projects/", headers={"Authorization": f"Bearer {token}"}
        )

        # Should be blocked (400, 403, or 404)
        assert response.status_code in [400, 403, 404]

    async def test_deleted_resources_not_accessible(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        user_org_a: User,
        project_org_a: Project,
    ):
        """Test that soft-deleted resources are not accessible"""
        from datetime import datetime

        # Soft delete the project
        project_org_a.deleted_at = datetime.now(UTC)
        project_org_a.deleted_by_id = user_org_a.id
        await db_session.commit()

        token = create_access_token(
            {
                "sub": str(user_org_a.id),
                "email": user_org_a.email,
                "name": user_org_a.full_name,
                "organization_id": user_org_a.organization_id,
                "role": user_org_a.role,
                "role_type": "tenant",
            }
        )

        # Try to access deleted project
        response = await async_client.get(
            f"/api/v1/projects/{project_org_a.id}", headers={"Authorization": f"Bearer {token}"}
        )

        # Should return 404 (not found)
        assert response.status_code == 404

    async def test_inactive_organization_blocked(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        org_a: Organization,
        user_org_a: User,
    ):
        """Test that users from inactive organizations are blocked"""
        # Set organization to inactive
        org_a.subscription_status = "cancelled"
        await db_session.commit()

        token = create_access_token(
            {
                "sub": str(user_org_a.id),
                "email": user_org_a.email,
                "name": user_org_a.full_name,
                "organization_id": user_org_a.organization_id,
                "role": user_org_a.role,
                "role_type": "tenant",
            }
        )

        # Try to access projects endpoint
        response = await async_client.get(
            "/api/v1/projects/", headers={"Authorization": f"Bearer {token}"}
        )

        # Should return 403 Forbidden
        assert response.status_code == 403
        assert "subscription" in response.json()["detail"].lower()
