"""
Performance tests for multi-tenant architecture

Tests to validate:
1. System performance with multiple tenants
2. Index effectiveness
3. Query performance isolation
"""

import asyncio

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.organization import Organization
from app.models.project import Project
from app.models.service import Service
from app.models.user import User
from app.repositories.factory import RepositoryFactory


@pytest.fixture
async def multiple_orgs(db_session: AsyncSession) -> list[Organization]:
    """Create multiple organizations for performance testing"""
    orgs = []
    for i in range(5):
        org = Organization(
            name=f"Performance Test Org {i}",
            slug=f"perf-test-org-{i}",
            subscription_plan="free",
            subscription_status="active",
        )
        db_session.add(org)
        orgs.append(org)
    await db_session.commit()
    for org in orgs:
        await db_session.refresh(org)
    return orgs


@pytest.fixture
async def users_per_org(
    db_session: AsyncSession, multiple_orgs: list[Organization]
) -> dict[int, list[User]]:
    """Create users for each organization"""
    users_by_org = {}
    for org in multiple_orgs:
        users = []
        for i in range(3):
            user = User(
                email=f"user{i}@{org.slug}.test",
                full_name=f"User {i}",
                hashed_password=get_password_hash("password123"),
                organization_id=org.id,
                role="product_manager",
            )
            db_session.add(user)
            users.append(user)
        await db_session.commit()
        for user in users:
            await db_session.refresh(user)
        users_by_org[org.id] = users
    return users_by_org


@pytest.fixture
async def projects_per_org(
    db_session: AsyncSession, multiple_orgs: list[Organization]
) -> dict[int, list[Project]]:
    """Create projects for each organization"""
    projects_by_org = {}
    for org in multiple_orgs:
        projects = []
        for i in range(10):
            project = Project(
                name=f"Project {i}", client_name=f"Client {i}", organization_id=org.id
            )
            db_session.add(project)
            projects.append(project)
        await db_session.commit()
        for project in projects:
            await db_session.refresh(project)
        projects_by_org[org.id] = projects
    return projects_by_org


@pytest.fixture
async def services_per_org(
    db_session: AsyncSession, multiple_orgs: list[Organization]
) -> dict[int, list[Service]]:
    """Create services for each organization"""
    services_by_org = {}
    for org in multiple_orgs:
        services = []
        for i in range(5):
            service = Service(
                name=f"Service {i}",
                description=f"Service {i} description",
                organization_id=org.id,
                default_margin_target=30.0,
                is_active=True,
            )
            db_session.add(service)
            services.append(service)
        await db_session.commit()
        for service in services:
            await db_session.refresh(service)
        services_by_org[org.id] = services
    return services_by_org


@pytest.mark.integration
class TestMultiTenantPerformance:
    """Performance tests for multi-tenant queries"""

    async def test_repository_query_isolation_performance(
        self,
        db_session: AsyncSession,
        multiple_orgs: list[Organization],
        projects_per_org: dict[int, list[Project]],
    ):
        """Test that repository queries are isolated and performant"""
        import time

        # Measure time to query projects for each organization
        times = []
        for org in multiple_orgs:
            start_time = time.time()
            repo = RepositoryFactory.create_project_repository(db_session, org.id)
            projects = await repo.get_all()
            end_time = time.time()

            times.append(end_time - start_time)

            # Verify correct isolation
            project_ids = [p.id for p in projects]
            expected_ids = [p.id for p in projects_per_org[org.id]]
            assert set(project_ids) == set(expected_ids)

            # Verify no cross-tenant data
            for other_org in multiple_orgs:
                if other_org.id != org.id:
                    other_project_ids = [p.id for p in projects_per_org[other_org.id]]
                    assert not any(pid in project_ids for pid in other_project_ids)

        # Average query time should be reasonable (< 100ms per query)
        avg_time = sum(times) / len(times)
        assert avg_time < 0.1, f"Average query time {avg_time} is too slow"

    async def test_index_effectiveness(
        self,
        db_session: AsyncSession,
        multiple_orgs: list[Organization],
        projects_per_org: dict[int, list[Project]],
    ):
        """Test that indexes are being used effectively"""
        import time

        # Query projects by organization_id (should use index)
        org = multiple_orgs[0]
        start_time = time.time()

        result = await db_session.execute(
            select(func.count(Project.id))
            .where(Project.organization_id == org.id)
            .where(Project.deleted_at.is_(None))
        )
        count = result.scalar()

        end_time = time.time()
        query_time = end_time - start_time

        assert count == len(projects_per_org[org.id])
        # Query should be fast with proper index
        assert query_time < 0.05, f"Indexed query took {query_time} seconds"

    async def test_concurrent_tenant_queries(
        self,
        db_session: AsyncSession,
        multiple_orgs: list[Organization],
        projects_per_org: dict[int, list[Project]],
    ):
        """Test that concurrent queries from different tenants work correctly"""

        async def query_org_projects(org_id: int):
            repo = RepositoryFactory.create_project_repository(db_session, org_id)
            projects = await repo.get_all()
            return [p.id for p in projects]

        # Execute queries concurrently for all organizations
        tasks = [query_org_projects(org.id) for org in multiple_orgs]
        results = await asyncio.gather(*tasks)

        # Verify each result contains only its own organization's projects
        for i, org in enumerate(multiple_orgs):
            project_ids = results[i]
            expected_ids = [p.id for p in projects_per_org[org.id]]
            assert set(project_ids) == set(expected_ids)

    async def test_large_dataset_isolation(
        self, db_session: AsyncSession, multiple_orgs: list[Organization]
    ):
        """Test isolation with larger datasets"""
        # Create many projects for first organization
        org_a = multiple_orgs[0]
        org_b = multiple_orgs[1]

        # Create 50 projects for org_a
        for i in range(50):
            project = Project(
                name=f"Large Dataset Project {i}",
                client_name=f"Client {i}",
                organization_id=org_a.id,
            )
            db_session.add(project)
        await db_session.commit()

        # Create 10 projects for org_b
        for i in range(10):
            project = Project(
                name=f"Small Dataset Project {i}",
                client_name=f"Client {i}",
                organization_id=org_b.id,
            )
            db_session.add(project)
        await db_session.commit()

        # Query org_a should return 50 projects
        repo_a = RepositoryFactory.create_project_repository(db_session, org_a.id)
        projects_a = await repo_a.get_all()
        assert len(projects_a) == 50

        # Query org_b should return 10 projects (not 50+10)
        repo_b = RepositoryFactory.create_project_repository(db_session, org_b.id)
        projects_b = await repo_b.get_all()
        assert len(projects_b) == 10

        # Verify no cross-contamination
        project_ids_a = {p.id for p in projects_a}
        project_ids_b = {p.id for p in projects_b}
        assert project_ids_a.isdisjoint(project_ids_b)
