"""
Integration tests to validate fixes for Problem 1: TenantContext in projects endpoints

Tests that list_projects() and delete_project() work correctly with TenantContext
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.organization import Organization
from app.models.project import Project
from app.models.service import Service
from app.models.user import User


@pytest.fixture
async def org_a(db_session: AsyncSession) -> Organization:
    """Create Organization A for testing"""
    org = Organization(
        name="Test Org A",
        slug="test-org-a",
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
    org = Organization(
        name="Test Org B",
        slug="test-org-b",
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
    user = User(
        email="user-a@test.com",
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
    user = User(
        email="user-b@test.com",
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
        description="Test service",
        organization_id=org_a.id,
        margin_target=0.40,
        billable_rate=100.0,
        is_active=True,
    )
    db_session.add(service)
    await db_session.commit()
    await db_session.refresh(service)
    return service


@pytest.fixture
async def project_org_a(db_session: AsyncSession, org_a: Organization) -> Project:
    """Create project for Organization A"""
    project = Project(
        name="Project Org A",
        client_name="Client A",
        organization_id=org_a.id,
        currency="USD",
        status="Draft",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def project_org_b(db_session: AsyncSession, org_b: Organization) -> Project:
    """Create project for Organization B"""
    project = Project(
        name="Project Org B",
        client_name="Client B",
        organization_id=org_b.id,
        currency="USD",
        status="Draft",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


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


@pytest.mark.integration
class TestListProjectsTenantFix:
    """Test that list_projects() works correctly with TenantContext"""

    async def test_list_projects_with_tenant_context(
        self,
        async_client: AsyncClient,
        user_org_a: User,
        project_org_a: Project,
        project_org_b: Project,
    ):
        """Test that list_projects() filters by tenant correctly"""
        headers = get_auth_headers(user_org_a)
        response = await async_client.get("/api/v1/projects/", headers=headers)

        # Should succeed (not NameError)
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data

        # Should only see projects from Org A
        project_ids = [p["id"] for p in data["items"]]
        assert project_org_a.id in project_ids
        assert project_org_b.id not in project_ids

    async def test_list_projects_empty_result(self, async_client: AsyncClient, user_org_a: User):
        """Test list_projects with no projects returns empty list"""
        headers = get_auth_headers(user_org_a)
        response = await async_client.get("/api/v1/projects/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


@pytest.mark.integration
class TestDeleteProjectTenantFix:
    """Test that delete_project() works correctly with TenantContext"""

    async def test_delete_project_with_tenant_context(
        self, async_client: AsyncClient, user_org_a: User, project_org_a: Project
    ):
        """Test that delete_project() works correctly with TenantContext"""
        headers = get_auth_headers(user_org_a)

        # Delete the project
        response = await async_client.delete(
            f"/api/v1/projects/{project_org_a.id}", headers=headers
        )

        # Should succeed (not NameError)
        assert response.status_code == 204

        # Verify project is soft deleted
        from app.core.database import get_db

        async for db in get_db():
            result = await db.execute(select(Project).where(Project.id == project_org_a.id))
            project = result.scalar_one_or_none()
            assert project is not None
            assert project.deleted_at is not None
            break

    async def test_delete_project_other_organization(
        self, async_client: AsyncClient, user_org_a: User, project_org_b: Project
    ):
        """Test that delete_project() cannot delete projects from other organizations"""
        headers = get_auth_headers(user_org_a)

        response = await async_client.delete(
            f"/api/v1/projects/{project_org_b.id}", headers=headers
        )

        # Should return 404 (project not found for this tenant)
        assert response.status_code == 404

        # Verify project is NOT deleted
        from app.core.database import get_db

        async for db in get_db():
            result = await db.execute(select(Project).where(Project.id == project_org_b.id))
            project = result.scalar_one_or_none()
            assert project is not None
            assert project.deleted_at is None
            break

    async def test_delete_nonexistent_project(self, async_client: AsyncClient, user_org_a: User):
        """Test delete_project with non-existent project ID"""
        headers = get_auth_headers(user_org_a)

        response = await async_client.delete("/api/v1/projects/99999", headers=headers)

        # Should return 404
        assert response.status_code == 404
