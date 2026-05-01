"""
Unit tests for plan limits validation edge cases
"""

from datetime import UTC

import pytest
from fastapi import HTTPException

from app.core.plan_limits import (
    check_limit,
    get_plan_limit,
    is_unlimited,
    validate_project_limit,
    validate_service_limit,
    validate_team_member_limit,
    validate_user_limit,
)
from app.models.organization import Organization
from app.models.project import Project
from app.models.service import Service
from app.models.team import TeamMember
from app.models.user import User


@pytest.mark.unit
class TestPlanLimits:
    """Tests for plan limits functions"""

    def test_get_plan_limit_free(self):
        """Test getting limits for free plan"""
        assert get_plan_limit("free", "max_users") == 1
        assert get_plan_limit("free", "max_projects") == 5
        assert get_plan_limit("free", "max_services") == 10
        assert get_plan_limit("free", "max_team_members") == 3

    def test_get_plan_limit_starter(self):
        """Test getting limits for starter plan"""
        assert get_plan_limit("starter", "max_users") == 5
        assert get_plan_limit("starter", "max_projects") == 10
        assert get_plan_limit("starter", "max_services") == 50
        assert get_plan_limit("starter", "max_team_members") == 10

    def test_get_plan_limit_professional(self):
        """Test getting limits for professional plan"""
        assert get_plan_limit("professional", "max_users") == 20
        assert get_plan_limit("professional", "max_projects") == 20
        assert get_plan_limit("professional", "max_services") == 200
        assert get_plan_limit("professional", "max_team_members") == 50

    def test_get_plan_limit_enterprise(self):
        """Test getting limits for enterprise plan (unlimited)"""
        assert get_plan_limit("enterprise", "max_users") == -1
        assert get_plan_limit("enterprise", "max_projects") == -1
        assert get_plan_limit("enterprise", "max_services") == -1
        assert get_plan_limit("enterprise", "max_team_members") == -1

    def test_get_plan_limit_invalid_plan(self):
        """Test getting limit for invalid plan (should default to free)"""
        assert get_plan_limit("invalid_plan", "max_users") == 1
        assert get_plan_limit("invalid_plan", "max_projects") == 5

    def test_get_plan_limit_invalid_type(self):
        """Test getting limit for invalid type (should return 0)"""
        assert get_plan_limit("free", "invalid_type") == 0

    def test_is_unlimited(self):
        """Test is_unlimited function"""
        assert is_unlimited(-1) is True
        assert is_unlimited(0) is False
        assert is_unlimited(1) is False
        assert is_unlimited(100) is False

    def test_check_limit_within_limit(self):
        """Test check_limit when within limit"""
        # Should not raise exception
        check_limit(current_count=3, limit=5, resource_name="projects", plan="free")
        check_limit(current_count=0, limit=5, resource_name="projects", plan="free")
        check_limit(current_count=4, limit=5, resource_name="projects", plan="free")

    def test_check_limit_at_limit(self):
        """Test check_limit when at limit (should raise exception)"""
        with pytest.raises(HTTPException) as exc_info:
            check_limit(current_count=5, limit=5, resource_name="projects", plan="free")

        assert exc_info.value.status_code == 403
        assert "limit exceeded" in exc_info.value.detail.lower()
        assert "current: 5" in exc_info.value.detail.lower()
        assert "limit: 5" in exc_info.value.detail.lower()

    def test_check_limit_exceeds_limit(self):
        """Test check_limit when exceeds limit"""
        with pytest.raises(HTTPException) as exc_info:
            check_limit(current_count=6, limit=5, resource_name="projects", plan="free")

        assert exc_info.value.status_code == 403
        assert "limit exceeded" in exc_info.value.detail.lower()

    def test_check_limit_unlimited(self):
        """Test check_limit with unlimited limit (-1)"""
        # Should not raise exception regardless of count
        check_limit(current_count=1000, limit=-1, resource_name="projects", plan="enterprise")
        check_limit(current_count=0, limit=-1, resource_name="projects", plan="enterprise")

    def test_check_limit_zero_limit(self):
        """Test check_limit with zero limit (edge case)"""
        with pytest.raises(HTTPException) as exc_info:
            check_limit(current_count=0, limit=0, resource_name="projects", plan="free")

        assert exc_info.value.status_code == 403


@pytest.mark.unit
class TestPlanLimitsEdgeCases:
    """Tests for edge cases in plan limits validation"""

    async def test_validate_user_limit_at_limit(self, db_session):
        """Test validate_user_limit when at limit"""
        # Create organization
        org = Organization(
            name="Test Org",
            slug="test-org-limit",
            subscription_plan="free",  # Free plan allows 1 user
            subscription_status="active",
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

        # Create 1 user (at limit)
        user = User(
            email="user1@test.com",
            full_name="User 1",
            hashed_password="hashed",
            organization_id=org.id,
            role="user",
            role_type="tenant",
        )
        db_session.add(user)
        await db_session.commit()

        # Try to validate (should raise exception)
        with pytest.raises(HTTPException) as exc_info:
            await validate_user_limit(org.id, org.subscription_plan, db_session)

        assert exc_info.value.status_code == 403
        assert "limit exceeded" in exc_info.value.detail.lower()

    async def test_validate_user_limit_below_limit(self, db_session):
        """Test validate_user_limit when below limit"""
        import uuid

        unique_id = str(uuid.uuid4())[:8]

        # Create organization
        org = Organization(
            name="Test Org",
            slug=f"test-org-below-{unique_id}",
            subscription_plan="starter",  # Starter plan allows 5 users
            subscription_status="active",
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

        # Create 2 users (below limit)
        for i in range(2):
            user = User(
                email=f"user{i}-{unique_id}@test.com",
                full_name=f"User {i}",
                hashed_password="hashed",
                organization_id=org.id,
                role="user",
                role_type="tenant",
            )
            db_session.add(user)
        await db_session.commit()

        # Should not raise exception
        await validate_user_limit(org.id, org.subscription_plan, db_session)

    async def test_validate_user_limit_unlimited(self, db_session):
        """Test validate_user_limit with unlimited plan"""
        import uuid

        unique_id = str(uuid.uuid4())[:8]

        # Create organization with enterprise plan
        org = Organization(
            name="Test Org",
            slug=f"test-org-unlimited-{unique_id}",
            subscription_plan="enterprise",  # Enterprise plan is unlimited
            subscription_status="active",
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

        # Create many users
        for i in range(100):
            user = User(
                email=f"user{i}-{unique_id}@test.com",
                full_name=f"User {i}",
                hashed_password="hashed",
                organization_id=org.id,
                role="user",
                role_type="tenant",
            )
            db_session.add(user)
        await db_session.commit()

        # Should not raise exception (unlimited)
        await validate_user_limit(org.id, org.subscription_plan, db_session)

    async def test_validate_project_limit_excludes_deleted(self, db_session):
        """Test that deleted projects are excluded from limit validation"""
        # Create organization
        org = Organization(
            name="Test Org",
            slug="test-org-deleted",
            subscription_plan="free",  # Free plan allows 5 projects
            subscription_status="active",
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

        # Create 4 active projects
        for i in range(4):
            project = Project(
                name=f"Project {i}", client_name=f"Client {i}", organization_id=org.id
            )
            db_session.add(project)

        # Create 2 deleted projects (should not count)
        from datetime import datetime

        for i in range(2):
            project = Project(
                name=f"Deleted Project {i}",
                client_name=f"Client {i}",
                organization_id=org.id,
                deleted_at=datetime.now(UTC),
            )
            db_session.add(project)

        await db_session.commit()

        # Should not raise exception (only 4 active projects, limit is 5)
        await validate_project_limit(org.id, org.subscription_plan, db_session)

    async def test_validate_service_limit_excludes_deleted(self, db_session):
        """Test that deleted services are excluded from limit validation"""
        # Create organization
        org = Organization(
            name="Test Org",
            slug="test-org-services",
            subscription_plan="free",  # Free plan allows 10 services
            subscription_status="active",
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

        # Create 9 active services
        for i in range(9):
            service = Service(
                name=f"Service {i}",
                description=f"Service {i} description",
                organization_id=org.id,
                default_margin_target=0.30,
                is_active=True,
            )
            db_session.add(service)

        # Create 2 deleted services (should not count)
        from datetime import datetime

        for i in range(2):
            service = Service(
                name=f"Deleted Service {i}",
                description=f"Service {i} description",
                organization_id=org.id,
                default_margin_target=0.30,
                is_active=True,
                deleted_at=datetime.now(UTC),
            )
            db_session.add(service)

        await db_session.commit()

        # Should not raise exception (only 9 active services, limit is 10)
        await validate_service_limit(org.id, org.subscription_plan, db_session)

    async def test_validate_team_member_limit_excludes_inactive(self, db_session):
        """Test that inactive team members are excluded from limit validation"""
        import uuid

        unique_id = str(uuid.uuid4())[:8]

        # Create organization
        org = Organization(
            name="Test Org",
            slug=f"test-org-team-{unique_id}",
            subscription_plan="free",  # Free plan allows 3 team members
            subscription_status="active",
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

        # Create 2 active team members
        for i in range(2):
            member = TeamMember(
                name=f"Member {i}",
                role="Developer",
                salary_monthly_brute=5000.0,
                currency="USD",
                organization_id=org.id,
                is_active=True,
            )
            db_session.add(member)

        # Create 2 inactive team members (should not count)
        for i in range(2):
            member = TeamMember(
                name=f"Inactive Member {i}",
                role="Developer",
                salary_monthly_brute=5000.0,
                currency="USD",
                organization_id=org.id,
                is_active=False,
            )
            db_session.add(member)

        await db_session.commit()

        # Should not raise exception (only 2 active members, limit is 3)
        await validate_team_member_limit(org.id, org.subscription_plan, db_session)
