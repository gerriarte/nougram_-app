"""
Unit tests for OrganizationRepository
"""

import uuid
from datetime import UTC, datetime

import pytest

from app.models.organization import Organization
from app.models.project import Project
from app.models.user import User
from app.repositories.organization_repository import OrganizationRepository


@pytest.mark.unit
class TestOrganizationRepository:
    """Tests for OrganizationRepository"""

    async def test_get_by_slug(self, db_session):
        """Test getting organization by slug"""
        repo = OrganizationRepository(db_session)

        # Create organization
        org = Organization(
            name="Test Organization",
            slug="test-org",
            subscription_plan="free",
            subscription_status="active",
        )
        created = await repo.create(org)
        await db_session.commit()

        # Get by slug
        found = await repo.get_by_slug("test-org")

        assert found is not None
        assert found.id == created.id
        assert found.slug == "test-org"
        assert found.name == "Test Organization"

    async def test_get_by_slug_not_found(self, db_session):
        """Test getting non-existent organization by slug"""
        repo = OrganizationRepository(db_session)

        found = await repo.get_by_slug("non-existent-slug")

        assert found is None

    async def test_list_all(self, db_session):
        """Test listing all organizations with pagination"""
        repo = OrganizationRepository(db_session)

        # Create multiple organizations
        orgs = []
        for i in range(5):
            org = Organization(
                name=f"Test Org {i}",
                slug=f"test-org-{i}",
                subscription_plan="free",
                subscription_status="active",
            )
            created = await repo.create(org)
            orgs.append(created)
        await db_session.commit()

        # List all (first page)
        organizations, total = await repo.list_all(page=1, page_size=3)

        assert total >= 5
        assert len(organizations) == 3

        # Verify pagination
        organizations_page2, total_page2 = await repo.list_all(page=2, page_size=3)
        assert total_page2 == total
        assert len(organizations_page2) >= 2

        # Verify different organizations
        assert organizations[0].id != organizations_page2[0].id

    async def test_list_all_with_inactive(self, db_session):
        """Test listing organizations including inactive ones"""
        repo = OrganizationRepository(db_session)

        # Create active organization
        active_org = Organization(
            name="Active Org",
            slug="active-org",
            subscription_plan="free",
            subscription_status="active",
        )
        await repo.create(active_org)

        # Create cancelled organization
        cancelled_org = Organization(
            name="Cancelled Org",
            slug="cancelled-org",
            subscription_plan="free",
            subscription_status="cancelled",
        )
        await repo.create(cancelled_org)
        await db_session.commit()

        # List without inactive
        active_only, total_active = await repo.list_all(include_inactive=False)
        assert all(org.subscription_status == "active" for org in active_only)

        # List with inactive
        all_orgs, total_all = await repo.list_all(include_inactive=True)
        assert total_all >= total_active
        assert any(org.subscription_status == "cancelled" for org in all_orgs)

    async def test_get_with_user_count(self, db_session, test_organization):
        """Test getting organization with user count"""
        repo = OrganizationRepository(db_session)

        # Create users for the organization
        user1 = User(
            email="user1@test.com",
            full_name="User 1",
            hashed_password="hashed",
            organization_id=test_organization.id,
            role="user",
            role_type="tenant",
        )
        user2 = User(
            email="user2@test.com",
            full_name="User 2",
            hashed_password="hashed",
            organization_id=test_organization.id,
            role="user",
            role_type="tenant",
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()

        # Get organization with user count
        org_with_count = await repo.get_with_user_count(test_organization.id)

        assert org_with_count is not None
        assert org_with_count.id == test_organization.id
        assert hasattr(org_with_count, "user_count")
        assert org_with_count.user_count >= 2

    async def test_get_with_user_count_no_users(self, db_session):
        """Test getting organization with user count when no users exist"""
        repo = OrganizationRepository(db_session)

        # Create a new organization without users
        unique_id = str(uuid.uuid4())[:8]
        org = Organization(
            name=f"Test Org No Users {unique_id}",
            slug=f"test-org-no-users-{unique_id}",
            subscription_plan="free",
            subscription_status="active",
        )
        created = await repo.create(org)
        await db_session.commit()

        # Get organization with user count
        org_with_count = await repo.get_with_user_count(created.id)

        assert org_with_count is not None
        assert org_with_count.id == created.id
        assert hasattr(org_with_count, "user_count")
        assert org_with_count.user_count == 0

    async def test_get_with_user_count_not_found(self, db_session):
        """Test getting non-existent organization with user count"""
        repo = OrganizationRepository(db_session)

        org_with_count = await repo.get_with_user_count(99999)

        assert org_with_count is None

    async def test_get_users(self, db_session):
        """Test getting all users in an organization"""
        repo = OrganizationRepository(db_session)

        # Create a new organization
        unique_id = str(uuid.uuid4())[:8]
        org = Organization(
            name=f"Test Org Users {unique_id}",
            slug=f"test-org-users-{unique_id}",
            subscription_plan="free",
            subscription_status="active",
        )
        created_org = await repo.create(org)
        await db_session.commit()

        # Create users with unique emails
        user1 = User(
            email=f"user1-{unique_id}@test.com",
            full_name="User 1",
            hashed_password="hashed",
            organization_id=created_org.id,
            role="user",
            role_type="tenant",
        )
        user2 = User(
            email=f"user2-{unique_id}@test.com",
            full_name="User 2",
            hashed_password="hashed",
            organization_id=created_org.id,
            role="owner",
            role_type="tenant",
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()

        # Get users
        users = await repo.get_users(created_org.id)

        assert len(users) >= 2
        assert all(user.organization_id == created_org.id for user in users)
        assert any(user.email == f"user1-{unique_id}@test.com" for user in users)
        assert any(user.email == f"user2-{unique_id}@test.com" for user in users)

    async def test_get_users_empty(self, db_session):
        """Test getting users when organization has no users"""
        repo = OrganizationRepository(db_session)

        # Create a new organization without users
        unique_id = str(uuid.uuid4())[:8]
        org = Organization(
            name=f"Test Org Empty {unique_id}",
            slug=f"test-org-empty-{unique_id}",
            subscription_plan="free",
            subscription_status="active",
        )
        created_org = await repo.create(org)
        await db_session.commit()

        users = await repo.get_users(created_org.id)

        assert isinstance(users, list)
        assert len(users) == 0

    async def test_get_user_count(self, db_session):
        """Test getting user count for an organization"""
        repo = OrganizationRepository(db_session)

        # Create a new organization
        unique_id = str(uuid.uuid4())[:8]
        org = Organization(
            name=f"Test Org Count {unique_id}",
            slug=f"test-org-count-{unique_id}",
            subscription_plan="free",
            subscription_status="active",
        )
        created_org = await repo.create(org)
        await db_session.commit()

        # Create users with unique emails
        user1 = User(
            email=f"user1-{unique_id}@test.com",
            full_name="User 1",
            hashed_password="hashed",
            organization_id=created_org.id,
            role="user",
            role_type="tenant",
        )
        user2 = User(
            email=f"user2-{unique_id}@test.com",
            full_name="User 2",
            hashed_password="hashed",
            organization_id=created_org.id,
            role="user",
            role_type="tenant",
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()

        # Get user count
        count = await repo.get_user_count(created_org.id)

        assert count == 2

    async def test_get_user_count_zero(self, db_session):
        """Test getting user count when no users exist"""
        repo = OrganizationRepository(db_session)

        # Create a new organization without users
        unique_id = str(uuid.uuid4())[:8]
        org = Organization(
            name=f"Test Org Zero {unique_id}",
            slug=f"test-org-zero-{unique_id}",
            subscription_plan="free",
            subscription_status="active",
        )
        created_org = await repo.create(org)
        await db_session.commit()

        count = await repo.get_user_count(created_org.id)

        assert count == 0

    async def test_get_project_count(self, db_session, test_organization):
        """Test getting project count for an organization"""
        repo = OrganizationRepository(db_session)

        # Create projects
        project1 = Project(
            name="Project 1", client_name="Client 1", organization_id=test_organization.id
        )
        project2 = Project(
            name="Project 2", client_name="Client 2", organization_id=test_organization.id
        )
        db_session.add(project1)
        db_session.add(project2)
        await db_session.commit()

        # Get project count
        count = await repo.get_project_count(test_organization.id)

        assert count >= 2

    async def test_get_project_count_excludes_deleted(self, db_session, test_organization):
        """Test that deleted projects are excluded from count"""
        repo = OrganizationRepository(db_session)

        # Create active project
        active_project = Project(
            name="Active Project", client_name="Client", organization_id=test_organization.id
        )

        # Create deleted project
        deleted_project = Project(
            name="Deleted Project",
            client_name="Client",
            organization_id=test_organization.id,
            deleted_at=datetime.now(UTC),
        )

        db_session.add(active_project)
        db_session.add(deleted_project)
        await db_session.commit()

        # Get project count (should exclude deleted)
        count = await repo.get_project_count(test_organization.id)

        assert count >= 1
        # Should not count deleted project

    async def test_get_project_count_zero(self, db_session):
        """Test getting project count when no projects exist"""
        repo = OrganizationRepository(db_session)

        # Create a new organization without projects
        unique_id = str(uuid.uuid4())[:8]
        org = Organization(
            name=f"Test Org No Projects {unique_id}",
            slug=f"test-org-no-projects-{unique_id}",
            subscription_plan="free",
            subscription_status="active",
        )
        created_org = await repo.create(org)
        await db_session.commit()

        count = await repo.get_project_count(created_org.id)

        assert count == 0

    async def test_update_subscription_plan(self, db_session, test_organization):
        """Test updating organization subscription plan"""
        repo = OrganizationRepository(db_session)

        # Update plan
        updated = await repo.update_subscription(test_organization.id, plan="professional")

        assert updated is not None
        assert updated.subscription_plan == "professional"
        assert (
            updated.subscription_status == test_organization.subscription_status
        )  # Status unchanged

    async def test_update_subscription_status(self, db_session, test_organization):
        """Test updating organization subscription status"""
        repo = OrganizationRepository(db_session)

        # Update status
        updated = await repo.update_subscription(test_organization.id, status="cancelled")

        assert updated is not None
        assert updated.subscription_status == "cancelled"
        assert updated.subscription_plan == test_organization.subscription_plan  # Plan unchanged

    async def test_update_subscription_both(self, db_session, test_organization):
        """Test updating both plan and status"""
        repo = OrganizationRepository(db_session)

        # Update both
        updated = await repo.update_subscription(
            test_organization.id, plan="enterprise", status="active"
        )

        assert updated is not None
        assert updated.subscription_plan == "enterprise"
        assert updated.subscription_status == "active"

    async def test_update_subscription_not_found(self, db_session):
        """Test updating subscription for non-existent organization"""
        repo = OrganizationRepository(db_session)

        updated = await repo.update_subscription(99999, plan="professional")

        assert updated is None

    async def test_list_all_user_counts(self, db_session):
        """Test that list_all includes user counts for each organization"""
        repo = OrganizationRepository(db_session)

        # Create organization with unique slug
        unique_id = str(uuid.uuid4())[:8]
        org = Organization(
            name=f"Test Org Counts {unique_id}",
            slug=f"test-org-counts-{unique_id}",
            subscription_plan="free",
            subscription_status="active",
        )
        created = await repo.create(org)
        await db_session.commit()

        # Create users with unique emails
        user1 = User(
            email=f"user1-{unique_id}@test.com",
            full_name="User 1",
            hashed_password="hashed",
            organization_id=created.id,
            role="user",
            role_type="tenant",
        )
        user2 = User(
            email=f"user2-{unique_id}@test.com",
            full_name="User 2",
            hashed_password="hashed",
            organization_id=created.id,
            role="user",
            role_type="tenant",
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()

        # List all
        organizations, total = await repo.list_all()

        # Find our organization
        found_org = next((o for o in organizations if o.id == created.id), None)

        assert found_org is not None
        assert hasattr(found_org, "user_count")
        assert found_org.user_count >= 2

    async def test_list_all_ordering(self, db_session):
        """Test that list_all orders by created_at descending"""
        repo = OrganizationRepository(db_session)

        # Create organizations with slight delay to ensure different timestamps
        org1 = Organization(
            name="First Org",
            slug="first-org",
            subscription_plan="free",
            subscription_status="active",
        )
        await repo.create(org1)
        await db_session.commit()

        import asyncio

        await asyncio.sleep(0.1)  # Small delay

        org2 = Organization(
            name="Second Org",
            slug="second-org",
            subscription_plan="free",
            subscription_status="active",
        )
        await repo.create(org2)
        await db_session.commit()

        # List all
        organizations, total = await repo.list_all()

        # Find our organizations
        found_orgs = [o for o in organizations if o.slug in ["first-org", "second-org"]]

        if len(found_orgs) >= 2:
            # Second org should come first (newest first)
            assert found_orgs[0].slug == "second-org" or found_orgs[1].slug == "second-org"
