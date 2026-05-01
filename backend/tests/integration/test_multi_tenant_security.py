"""
Integration tests for multi-tenant security and data isolation

These tests validate:
1. JWT tokens include organization_id
2. Token organization_id validation prevents unauthorized access
3. Data isolation between tenants
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, decode_access_token
from app.models.organization import Organization
from app.models.project import Project
from app.models.service import Service
from app.models.user import User


@pytest.mark.integration
class TestMultiTenantJWT:
    """Tests for JWT multi-tenant functionality"""

    async def test_login_token_includes_organization_id(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test that login token includes organization_id in payload"""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert "organization_id" in data["user"]

        # Decode token and verify organization_id is in payload
        token = data["access_token"]
        payload = decode_access_token(token)

        assert payload is not None
        assert "organization_id" in payload
        assert payload["organization_id"] == test_user.organization_id
        assert payload["sub"] == str(test_user.id)

    async def test_token_with_wrong_organization_id_rejected(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test that token with wrong organization_id is rejected"""
        # Create token with wrong organization_id
        wrong_org_id = 99999
        token_data = {
            "sub": str(test_user.id),
            "email": test_user.email,
            "name": test_user.full_name,
            "organization_id": wrong_org_id,  # Wrong org ID
            "role": test_user.role,
            "role_type": "tenant",
        }
        token = create_access_token(token_data)

        # Try to access protected endpoint
        response = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        # Should be rejected due to organization mismatch
        assert response.status_code == 401
        data = response.json()
        assert "mismatch" in data["detail"].lower() or "unauthorized" in data["detail"].lower()

    async def test_token_with_valid_organization_id_accepted(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test that token with valid organization_id is accepted"""
        token_data = {
            "sub": str(test_user.id),
            "email": test_user.email,
            "name": test_user.full_name,
            "organization_id": test_user.organization_id,
            "role": test_user.role,
            "role_type": "tenant",
        }
        token = create_access_token(token_data)

        response = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email

    async def test_old_token_without_organization_id_still_works(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test backward compatibility: old tokens without organization_id still work"""
        # Create token without organization_id (old format)
        token_data = {
            "sub": str(test_user.id),
            "email": test_user.email,
            "name": test_user.full_name,
            "role": test_user.role,
            "role_type": "tenant",
        }
        token = create_access_token(token_data)

        # Should still work (backward compatibility)
        response = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        # Should work if user has organization_id
        if test_user.organization_id is not None:
            assert response.status_code == 200
        else:
            # If user has no org, might fail in other validations
            pass


@pytest.mark.integration
class TestMultiTenantDataIsolation:
    """Tests for data isolation between tenants"""

    async def test_user_cannot_access_other_tenant_projects(
        self, async_client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        """Test that user from Org A cannot access projects from Org B"""
        # Create another organization
        org_b = Organization(
            name="Organization B",
            slug="org-b-test-isolation",
            subscription_plan="free",
            subscription_status="active",
        )
        db_session.add(org_b)
        await db_session.flush()

        # Create user for Org B
        from app.core.security import get_password_hash

        user_b = User(
            email="userb@example.com",
            full_name="User B",
            hashed_password=get_password_hash("password123"),
            organization_id=org_b.id,
        )
        db_session.add(user_b)
        await db_session.flush()

        # Create project for Org B
        project_b = Project(name="Project B", client_name="Client B", organization_id=org_b.id)
        db_session.add(project_b)
        await db_session.commit()
        await db_session.refresh(project_b)

        # Create token for user A
        token_a = create_access_token(
            {
                "sub": str(test_user.id),
                "email": test_user.email,
                "organization_id": test_user.organization_id,
            }
        )

        # Try to access project B with user A's token
        response = await async_client.get(
            f"/api/v1/projects/{project_b.id}", headers={"Authorization": f"Bearer {token_a}"}
        )

        # Should not be able to access (404 or 403)
        assert response.status_code in [404, 403]

        # Cleanup
        await db_session.delete(project_b)
        await db_session.delete(user_b)
        await db_session.delete(org_b)
        await db_session.commit()

    async def test_user_cannot_access_other_tenant_services(
        self, async_client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        """Test that user from Org A cannot access services from Org B"""
        # Create another organization
        org_b = Organization(
            name="Organization B",
            slug="org-b-test-isolation-2",
            subscription_plan="free",
            subscription_status="active",
        )
        db_session.add(org_b)
        await db_session.flush()

        # Create service for Org B
        service_b = Service(
            name="Service B",
            description="Service from Org B",
            organization_id=org_b.id,
            default_margin_target=0.30,
            is_active=True,
        )
        db_session.add(service_b)
        await db_session.commit()
        await db_session.refresh(service_b)

        # Create token for user A
        token_a = create_access_token(
            {
                "sub": str(test_user.id),
                "email": test_user.email,
                "organization_id": test_user.organization_id,
            }
        )

        # Try to access service B with user A's token
        response = await async_client.get(
            f"/api/v1/services/{service_b.id}", headers={"Authorization": f"Bearer {token_a}"}
        )

        # Should not be able to access (404 or 403)
        assert response.status_code in [404, 403]

        # Cleanup
        await db_session.delete(service_b)
        await db_session.delete(org_b)
        await db_session.commit()

    async def test_user_can_only_list_own_tenant_data(
        self, async_client: AsyncClient, db_session: AsyncSession, test_user: User
    ):
        """Test that listing endpoints only return data from user's tenant"""
        # Create another organization
        org_b = Organization(
            name="Organization B",
            slug="org-b-test-isolation-3",
            subscription_plan="free",
            subscription_status="active",
        )
        db_session.add(org_b)
        await db_session.flush()

        # Create project for Org B
        project_b = Project(name="Project B", client_name="Client B", organization_id=org_b.id)
        db_session.add(project_b)

        # Create project for Org A (test_user's org)
        project_a = Project(
            name="Project A", client_name="Client A", organization_id=test_user.organization_id
        )
        db_session.add(project_a)
        await db_session.commit()

        # Create token for user A
        token_a = create_access_token(
            {
                "sub": str(test_user.id),
                "email": test_user.email,
                "organization_id": test_user.organization_id,
            }
        )

        # List projects with user A's token
        response = await async_client.get(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {token_a}"},
            params={"page": 1, "page_size": 100},
        )

        assert response.status_code == 200
        data = response.json()

        # Should only see project A, not project B
        project_ids = [p["id"] for p in data.get("items", [])]
        assert project_a.id in project_ids
        assert project_b.id not in project_ids

        # Cleanup
        await db_session.delete(project_b)
        await db_session.delete(project_a)
        await db_session.delete(org_b)
        await db_session.commit()


@pytest.mark.integration
class TestMultiTenantLoginValidation:
    """Tests for login validation with organization_id"""

    async def test_login_without_organization_fails(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that login fails if user has no organization_id"""
        from app.core.security import get_password_hash
        from app.models.user import User

        # Create user without organization_id
        user_no_org = User(
            email="noorg@example.com",
            full_name="No Org User",
            hashed_password=get_password_hash("password123"),
            organization_id=None,  # No organization
        )
        db_session.add(user_no_org)
        await db_session.commit()
        await db_session.refresh(user_no_org)

        # Try to login
        response = await async_client.post(
            "/api/v1/auth/login", json={"email": "noorg@example.com", "password": "password123"}
        )

        # Should fail because user has no organization
        assert response.status_code == 400
        data = response.json()
        assert "organización" in data["detail"].lower() or "organization" in data["detail"].lower()

        # Cleanup
        await db_session.delete(user_no_org)
        await db_session.commit()
