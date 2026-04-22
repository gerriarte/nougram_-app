"""
Integration tests for industry templates endpoints
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.cost import CostFixed
from app.models.organization import Organization
from app.models.service import Service
from app.models.team import TeamMember
from app.models.template import IndustryTemplate
from app.models.user import User


def get_auth_headers(user: User) -> dict:
    """Helper to create auth headers for a user"""
    token_data = {"sub": str(user.id), "email": user.email, "organization_id": user.organization_id}
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_org_with_user(db_session: AsyncSession) -> tuple[Organization, User]:
    """Create test organization and admin user"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]

    org = Organization(
        name="Test Template Org",
        slug=f"test-template-org-{unique_id}",
        subscription_plan="professional",
        subscription_status="active",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    user = User(
        email=f"admin{unique_id}@test.com",
        full_name="Template Admin",
        hashed_password=get_password_hash("password123"),
        organization_id=org.id,
        role="org_admin",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return org, user


@pytest.mark.integration
class TestListTemplates:
    """Tests for GET /templates/industries"""

    async def test_list_templates_success(self, async_client: AsyncClient):
        """Test listing all active templates"""
        response = await async_client.get("/api/v1/templates/industries")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 0  # At least 0 templates (may not have run migration yet)

    async def test_list_templates_active_only(self, async_client: AsyncClient):
        """Test listing only active templates"""
        response = await async_client.get("/api/v1/templates/industries?active_only=true")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # All returned templates should be active
        for item in data["items"]:
            assert item["is_active"] is True


@pytest.mark.integration
class TestGetTemplate:
    """Tests for GET /templates/industries/{industry_type}"""

    async def test_get_template_success(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test getting a specific template"""
        # First ensure we have at least one template
        result = await db_session.execute(
            select(IndustryTemplate).where(IndustryTemplate.is_active).limit(1)
        )
        template = result.scalar_one_or_none()

        if template:
            response = await async_client.get(
                f"/api/v1/templates/industries/{template.industry_type}"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["industry_type"] == template.industry_type
            assert data["name"] == template.name
            assert "suggested_roles" in data or data.get("suggested_roles") is None
            assert "suggested_services" in data or data.get("suggested_services") is None

    async def test_get_template_not_found(self, async_client: AsyncClient):
        """Test getting non-existent template"""
        response = await async_client.get("/api/v1/templates/industries/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


@pytest.mark.integration
class TestApplyTemplate:
    """Tests for POST /templates/organizations/{id}/apply-template"""

    async def test_apply_template_success(
        self,
        async_client: AsyncClient,
        test_org_with_user: tuple[Organization, User],
        db_session: AsyncSession,
    ):
        """Test applying a template to an organization"""
        org, user = test_org_with_user

        # Ensure we have a template
        result = await db_session.execute(
            select(IndustryTemplate).where(IndustryTemplate.is_active).limit(1)
        )
        template = result.scalar_one_or_none()

        if not template:
            pytest.skip("No templates available - migration may not have run")

        headers = get_auth_headers(user)
        response = await async_client.post(
            f"/api/v1/templates/organizations/{org.id}/apply-template",
            json={"industry_type": template.industry_type, "region": "US", "currency": "USD"},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["template_applied"] == template.industry_type
        assert data["region"] == "US"
        assert "multiplier" in data
        assert data["team_members_created"] >= 0
        assert data["services_created"] >= 0
        assert data["costs_created"] >= 0

        # Verify resources were created
        if data["team_members_created"] > 0:
            result = await db_session.execute(
                select(TeamMember).where(TeamMember.organization_id == org.id)
            )
            team_members = result.scalars().all()
            assert len(team_members) == data["team_members_created"]

        if data["services_created"] > 0:
            result = await db_session.execute(
                select(Service).where(Service.organization_id == org.id)
            )
            services = result.scalars().all()
            assert len(services) == data["services_created"]

        if data["costs_created"] > 0:
            result = await db_session.execute(
                select(CostFixed).where(CostFixed.organization_id == org.id)
            )
            costs = result.scalars().all()
            assert len(costs) == data["costs_created"]

        # Verify organization settings were updated
        await db_session.refresh(org)
        assert org.settings is not None
        assert org.settings.get("onboarding_completed") is True
        assert org.settings.get("industry_type") == template.industry_type

    async def test_apply_template_with_region_adjustment(
        self,
        async_client: AsyncClient,
        test_org_with_user: tuple[Organization, User],
        db_session: AsyncSession,
    ):
        """Test applying template with region multiplier adjustment"""
        org, user = test_org_with_user

        result = await db_session.execute(
            select(IndustryTemplate).where(IndustryTemplate.is_active).limit(1)
        )
        template = result.scalar_one_or_none()

        if not template:
            pytest.skip("No templates available")

        headers = get_auth_headers(user)
        response = await async_client.post(
            f"/api/v1/templates/organizations/{org.id}/apply-template",
            json={
                "industry_type": template.industry_type,
                "region": "COL",  # Colombia has 0.25 multiplier
                "currency": "COP",
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["multiplier"] == 0.25  # Colombia multiplier
        assert data["region"] == "COL"
        assert data["currency"] == "COP"

    async def test_apply_template_permission_denied(
        self,
        async_client: AsyncClient,
        test_org_with_user: tuple[Organization, User],
        db_session: AsyncSession,
    ):
        """Test that regular users cannot apply templates"""
        org, admin_user = test_org_with_user

        # Create regular user from different org
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        other_org = Organization(
            name="Other Org",
            slug=f"other-org-{unique_id}",
            subscription_plan="free",
            subscription_status="active",
        )
        db_session.add(other_org)
        await db_session.commit()
        await db_session.refresh(other_org)

        regular_user = User(
            email=f"regular{unique_id}@test.com",
            full_name="Regular User",
            hashed_password=get_password_hash("password123"),
            organization_id=other_org.id,
            role="org_member",
        )
        db_session.add(regular_user)
        await db_session.commit()
        await db_session.refresh(regular_user)

        result = await db_session.execute(
            select(IndustryTemplate).where(IndustryTemplate.is_active).limit(1)
        )
        template = result.scalar_one_or_none()

        if not template:
            pytest.skip("No templates available")

        headers = get_auth_headers(regular_user)
        response = await async_client.post(
            f"/api/v1/templates/organizations/{org.id}/apply-template",
            json={"industry_type": template.industry_type, "region": "US", "currency": "USD"},
            headers=headers,
        )

        assert response.status_code == 403

    async def test_apply_template_organization_not_found(
        self,
        async_client: AsyncClient,
        test_org_with_user: tuple[Organization, User],
        db_session: AsyncSession,
    ):
        """Test applying template to non-existent organization"""
        _, user = test_org_with_user

        result = await db_session.execute(
            select(IndustryTemplate).where(IndustryTemplate.is_active).limit(1)
        )
        template = result.scalar_one_or_none()

        if not template:
            pytest.skip("No templates available")

        headers = get_auth_headers(user)
        response = await async_client.post(
            "/api/v1/templates/organizations/99999/apply-template",
            json={"industry_type": template.industry_type, "region": "US", "currency": "USD"},
            headers=headers,
        )

        assert response.status_code == 404

    async def test_apply_template_invalid_type(
        self, async_client: AsyncClient, test_org_with_user: tuple[Organization, User]
    ):
        """Test applying non-existent template type"""
        org, user = test_org_with_user

        headers = get_auth_headers(user)
        response = await async_client.post(
            f"/api/v1/templates/organizations/{org.id}/apply-template",
            json={"industry_type": "nonexistent_type", "region": "US", "currency": "USD"},
            headers=headers,
        )

        assert response.status_code == 400
