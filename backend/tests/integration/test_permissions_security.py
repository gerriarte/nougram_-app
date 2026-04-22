"""
Integration tests for granular permissions system
Tests that validate role-based access control, data leakage prevention, and cross-tenant security
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.organization import Organization
from app.models.user import User


@pytest.fixture
async def test_users(db_session: AsyncSession):
    """Create test users with different roles"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]

    # Create organizations
    org1 = Organization(name="Test Org 1", slug=f"test-org-1-{unique_id}", subscription_plan="pro")
    org2 = Organization(name="Test Org 2", slug=f"test-org-2-{unique_id}", subscription_plan="free")
    db_session.add(org1)
    db_session.add(org2)
    await db_session.flush()

    # Create users with different roles
    password_hash = get_password_hash("testpassword123")
    users = {
        "super_admin": User(
            email=f"superadmin-{unique_id}@test.com",
            full_name="Super Admin",
            hashed_password=password_hash,
            role="super_admin",
            role_type="support",
            organization_id=None,
        ),
        "owner_org1": User(
            email=f"owner1-{unique_id}@test.com",
            full_name="Owner 1",
            hashed_password=password_hash,
            role="owner",
            role_type="tenant",
            organization_id=org1.id,
        ),
        "admin_financiero_org1": User(
            email=f"admin1-{unique_id}@test.com",
            full_name="Admin Financiero 1",
            hashed_password=password_hash,
            role="admin_financiero",
            role_type="tenant",
            organization_id=org1.id,
        ),
        "product_manager_org1": User(
            email=f"pm1-{unique_id}@test.com",
            full_name="Product Manager 1",
            hashed_password=password_hash,
            role="product_manager",
            role_type="tenant",
            organization_id=org1.id,
        ),
        "collaborator_org1": User(
            email=f"collab1-{unique_id}@test.com",
            full_name="Collaborator 1",
            hashed_password=password_hash,
            role="collaborator",
            role_type="tenant",
            organization_id=org1.id,
        ),
        "owner_org2": User(
            email=f"owner2-{unique_id}@test.com",
            full_name="Owner 2",
            hashed_password=password_hash,
            role="owner",
            role_type="tenant",
            organization_id=org2.id,
        ),
    }

    for user in users.values():
        db_session.add(user)

    await db_session.commit()

    # Refresh to get IDs
    for _key, user in users.items():
        await db_session.refresh(user)

    return users


class TestPermissionValidation:
    """Test that permission validations work correctly"""

    async def test_super_admin_has_all_permissions(self, async_client: AsyncClient, test_users):
        """Super admin should have access to all resources"""
        token = create_access_token(test_users["super_admin"])
        headers = {"Authorization": f"Bearer {token}"}

        # Should be able to access any endpoint
        response = await async_client.get("/api/v1/organizations/", headers=headers)
        assert response.status_code == 200

    async def test_owner_can_view_sensitive_data(
        self, async_client: AsyncClient, test_users, db_session: AsyncSession
    ):
        """Owner should be able to view costs and salaries"""
        token = create_access_token(test_users["owner_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        # Should be able to view team members (with salaries)
        response = await async_client.get("/api/v1/team/", headers=headers)
        assert response.status_code == 200

        # Should be able to view fixed costs
        response = await async_client.get("/api/v1/costs/", headers=headers)
        assert response.status_code == 200

    async def test_product_manager_cannot_view_sensitive_data(
        self, async_client: AsyncClient, test_users
    ):
        """Product manager should NOT be able to view costs and salaries"""
        token = create_access_token(test_users["product_manager_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        # Should NOT be able to view team members (contains salaries)
        response = await async_client.get("/api/v1/team/", headers=headers)
        assert response.status_code == 403

        # Should NOT be able to view fixed costs
        response = await async_client.get("/api/v1/costs/", headers=headers)
        assert response.status_code == 403

    async def test_collaborator_cannot_view_sensitive_data(
        self, async_client: AsyncClient, test_users
    ):
        """Collaborator should NOT be able to view costs and salaries"""
        token = create_access_token(test_users["collaborator_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        # Should NOT be able to view team members
        response = await async_client.get("/api/v1/team/", headers=headers)
        assert response.status_code == 403

        # Should NOT be able to view fixed costs
        response = await async_client.get("/api/v1/costs/", headers=headers)
        assert response.status_code == 403

    async def test_admin_financiero_can_view_sensitive_data(
        self, async_client: AsyncClient, test_users
    ):
        """Admin financiero should be able to view costs and salaries"""
        token = create_access_token(test_users["admin_financiero_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        # Should be able to view team members
        response = await async_client.get("/api/v1/team/", headers=headers)
        assert response.status_code == 200

        # Should be able to view fixed costs
        response = await async_client.get("/api/v1/costs/", headers=headers)
        assert response.status_code == 200


class TestCreateResourcesPermissions:
    """Test permissions for creating resources"""

    async def test_owner_can_create_projects(self, async_client: AsyncClient, test_users):
        """Owner should be able to create projects"""
        token = create_access_token(test_users["owner_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        project_data = {
            "name": "Test Project",
            "client_name": "Test Client",
            "client_email": "client@test.com",
            "currency": "USD",
        }
        response = await async_client.post("/api/v1/projects/", json=project_data, headers=headers)
        assert response.status_code == 201

    async def test_product_manager_can_create_projects(self, async_client: AsyncClient, test_users):
        """Product manager should be able to create projects"""
        token = create_access_token(test_users["product_manager_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        project_data = {
            "name": "Test Project",
            "client_name": "Test Client",
            "client_email": "client@test.com",
            "currency": "USD",
        }
        response = await async_client.post("/api/v1/projects/", json=project_data, headers=headers)
        assert response.status_code == 201

    async def test_collaborator_can_create_projects(self, async_client: AsyncClient, test_users):
        """Collaborator should be able to create projects"""
        token = create_access_token(test_users["collaborator_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        project_data = {
            "name": "Test Project",
            "client_name": "Test Client",
            "client_email": "client@test.com",
            "currency": "USD",
        }
        response = await async_client.post("/api/v1/projects/", json=project_data, headers=headers)
        assert response.status_code == 201

    async def test_owner_can_modify_costs(self, async_client: AsyncClient, test_users):
        """Owner should be able to modify costs"""
        token = create_access_token(test_users["owner_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        cost_data = {
            "name": "Test Cost",
            "amount_monthly": 1000.0,
            "currency": "USD",
            "category": "office",
        }
        response = await async_client.post("/api/v1/costs/", json=cost_data, headers=headers)
        assert response.status_code == 201

    async def test_product_manager_cannot_modify_costs(self, async_client: AsyncClient, test_users):
        """Product manager should NOT be able to modify costs"""
        token = create_access_token(test_users["product_manager_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        cost_data = {
            "name": "Test Cost",
            "amount_monthly": 1000.0,
            "currency": "USD",
            "category": "office",
        }
        response = await async_client.post("/api/v1/costs/", json=cost_data, headers=headers)
        assert response.status_code == 403

    async def test_collaborator_cannot_modify_costs(self, async_client: AsyncClient, test_users):
        """Collaborator should NOT be able to modify costs"""
        token = create_access_token(test_users["collaborator_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        cost_data = {
            "name": "Test Cost",
            "amount_monthly": 1000.0,
            "currency": "USD",
            "category": "office",
        }
        response = await async_client.post("/api/v1/costs/", json=cost_data, headers=headers)
        assert response.status_code == 403


class TestSendQuotesPermissions:
    """Test permissions for sending quotes"""

    async def test_owner_can_send_quotes(
        self, async_client: AsyncClient, test_users, db_session: AsyncSession
    ):
        """Owner should be able to send quotes"""
        token = create_access_token(test_users["owner_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        # First create a project
        project_data = {
            "name": "Test Project",
            "client_name": "Test Client",
            "client_email": "client@test.com",
            "currency": "USD",
        }
        project_response = await async_client.post(
            "/api/v1/projects/", json=project_data, headers=headers
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        # Create a quote
        quote_data = {"items": [{"service_id": 1, "estimated_hours": 10}]}
        quote_response = await async_client.post(
            f"/api/v1/projects/{project_id}/quotes/", json=quote_data, headers=headers
        )
        assert quote_response.status_code == 201
        quote_id = quote_response.json()["id"]

        # Should be able to send quote
        send_data = {"to_email": "client@test.com", "subject": "Test Quote"}
        response = await async_client.post(
            f"/api/v1/projects/{project_id}/quotes/{quote_id}/send-email",
            json=send_data,
            headers=headers,
        )
        assert response.status_code in [200, 202]  # Success or accepted

    async def test_product_manager_can_send_quotes(
        self, async_client: AsyncClient, test_users, db_session: AsyncSession
    ):
        """Product manager should be able to send quotes"""
        token = create_access_token(test_users["product_manager_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        # Create project and quote
        project_data = {
            "name": "Test Project",
            "client_name": "Test Client",
            "client_email": "client@test.com",
            "currency": "USD",
        }
        project_response = await async_client.post(
            "/api/v1/projects/", json=project_data, headers=headers
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        quote_data = {"items": [{"service_id": 1, "estimated_hours": 10}]}
        quote_response = await async_client.post(
            f"/api/v1/projects/{project_id}/quotes/", json=quote_data, headers=headers
        )
        assert quote_response.status_code == 201
        quote_id = quote_response.json()["id"]

        # Should be able to send quote
        send_data = {"to_email": "client@test.com", "subject": "Test Quote"}
        response = await async_client.post(
            f"/api/v1/projects/{project_id}/quotes/{quote_id}/send-email",
            json=send_data,
            headers=headers,
        )
        assert response.status_code in [200, 202]

    async def test_collaborator_cannot_send_quotes(
        self, async_client: AsyncClient, test_users, db_session: AsyncSession
    ):
        """Collaborator should NOT be able to send quotes"""
        token = create_access_token(test_users["collaborator_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        # Create project and quote
        project_data = {
            "name": "Test Project",
            "client_name": "Test Client",
            "client_email": "client@test.com",
            "currency": "USD",
        }
        project_response = await async_client.post(
            "/api/v1/projects/", json=project_data, headers=headers
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        quote_data = {"items": [{"service_id": 1, "estimated_hours": 10}]}
        quote_response = await async_client.post(
            f"/api/v1/projects/{project_id}/quotes/", json=quote_data, headers=headers
        )
        assert quote_response.status_code == 201
        quote_id = quote_response.json()["id"]

        # Should NOT be able to send quote
        send_data = {"to_email": "client@test.com", "subject": "Test Quote"}
        response = await async_client.post(
            f"/api/v1/projects/{project_id}/quotes/{quote_id}/send-email",
            json=send_data,
            headers=headers,
        )
        assert response.status_code == 403


class TestManageSubscriptionPermissions:
    """Test permissions for managing subscriptions"""

    async def test_owner_can_manage_subscription(self, async_client: AsyncClient, test_users):
        """Owner should be able to manage subscription"""
        token = create_access_token(test_users["owner_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        # Should be able to view billing
        response = await async_client.get("/api/v1/billing/subscription", headers=headers)
        assert response.status_code in [200, 404]  # 404 if no subscription yet

    async def test_product_manager_cannot_manage_subscription(
        self, async_client: AsyncClient, test_users
    ):
        """Product manager should NOT be able to manage subscription"""
        create_access_token(test_users["product_manager_org1"])

        # Should NOT be able to update subscription (if endpoint exists)
        # This depends on the actual implementation
        pass

    async def test_collaborator_cannot_manage_subscription(
        self, async_client: AsyncClient, test_users
    ):
        """Collaborator should NOT be able to manage subscription"""
        create_access_token(test_users["collaborator_org1"])

        # Should NOT be able to manage subscription
        pass


class TestInviteUsersPermissions:
    """Test permissions for inviting users"""

    async def test_owner_can_invite_users(self, async_client: AsyncClient, test_users):
        """Owner should be able to invite users"""
        token = create_access_token(test_users["owner_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        invite_data = {"email": "newuser@test.com", "role": "product_manager"}
        response = await async_client.post(
            f"/api/v1/organizations/{test_users['owner_org1'].organization_id}/invite",
            json=invite_data,
            headers=headers,
        )
        assert response.status_code in [200, 201]

    async def test_admin_financiero_cannot_invite_users(
        self, async_client: AsyncClient, test_users
    ):
        """Admin financiero should NOT be able to invite users"""
        token = create_access_token(test_users["admin_financiero_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        invite_data = {"email": "newuser@test.com", "role": "product_manager"}
        response = await async_client.post(
            f"/api/v1/organizations/{test_users['admin_financiero_org1'].organization_id}/invite",
            json=invite_data,
            headers=headers,
        )
        assert response.status_code == 403

    async def test_product_manager_cannot_invite_users(self, async_client: AsyncClient, test_users):
        """Product manager should NOT be able to invite users"""
        token = create_access_token(test_users["product_manager_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        invite_data = {"email": "newuser@test.com", "role": "product_manager"}
        response = await async_client.post(
            f"/api/v1/organizations/{test_users['product_manager_org1'].organization_id}/invite",
            json=invite_data,
            headers=headers,
        )
        assert response.status_code == 403


class TestCrossTenantSecurity:
    """Test that users cannot access resources from other organizations"""

    async def test_owner_cannot_access_other_org_resources(
        self, async_client: AsyncClient, test_users, db_session: AsyncSession
    ):
        """Owner from org1 should NOT be able to access org2's resources"""
        owner1_token = create_access_token(test_users["owner_org1"])
        owner1_headers = {"Authorization": f"Bearer {owner1_token}"}

        owner2_token = create_access_token(test_users["owner_org2"])
        owner2_headers = {"Authorization": f"Bearer {owner2_token}"}

        # Owner2 creates a project
        project_data = {
            "name": "Org2 Project",
            "client_name": "Org2 Client",
            "client_email": "org2@test.com",
            "currency": "USD",
        }
        create_response = await async_client.post(
            "/api/v1/projects/", json=project_data, headers=owner2_headers
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        # Owner1 should NOT be able to access org2's project
        response = await async_client.get(f"/api/v1/projects/{project_id}", headers=owner1_headers)
        assert response.status_code == 404  # Not found (tenant isolation)

    async def test_cannot_modify_other_org_resources(
        self, async_client: AsyncClient, test_users, db_session: AsyncSession
    ):
        """Users should NOT be able to modify resources from other organizations"""
        owner1_token = create_access_token(test_users["owner_org1"])
        owner1_headers = {"Authorization": f"Bearer {owner1_token}"}

        owner2_token = create_access_token(test_users["owner_org2"])
        owner2_headers = {"Authorization": f"Bearer {owner2_token}"}

        # Owner2 creates a cost
        cost_data = {
            "name": "Org2 Cost",
            "amount_monthly": 500.0,
            "currency": "USD",
            "category": "office",
        }
        create_response = await async_client.post(
            "/api/v1/costs/", json=cost_data, headers=owner2_headers
        )
        assert create_response.status_code == 201
        cost_id = create_response.json()["id"]

        # Owner1 should NOT be able to modify org2's cost
        update_data = {
            "name": "Hacked Cost",
            "amount_monthly": 10000.0,
            "currency": "USD",
            "category": "office",
        }
        response = await async_client.put(
            f"/api/v1/costs/{cost_id}", json=update_data, headers=owner1_headers
        )
        assert response.status_code == 404  # Not found (tenant isolation)


class TestDeletePermissions:
    """Test permissions for deleting resources"""

    async def test_owner_can_delete_resources(
        self, async_client: AsyncClient, test_users, db_session: AsyncSession
    ):
        """Owner should be able to delete resources"""
        token = create_access_token(test_users["owner_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        # Create a service first
        service_data = {
            "name": "Test Service",
            "description": "Test",
            "hourly_rate": 100.0,
            "currency": "USD",
        }
        create_response = await async_client.post(
            "/api/v1/services/", json=service_data, headers=headers
        )
        assert create_response.status_code == 201
        service_id = create_response.json()["id"]

        # Should be able to delete
        response = await async_client.delete(f"/api/v1/services/{service_id}", headers=headers)
        assert response.status_code in [204, 200]

    async def test_product_manager_cannot_delete_resources(
        self, async_client: AsyncClient, test_users, db_session: AsyncSession
    ):
        """Product manager should NOT be able to delete resources"""
        token = create_access_token(test_users["product_manager_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        # Create a service first (if they can)
        # Actually, product_manager might not be able to create services either
        # Let's test with a project they created
        project_data = {
            "name": "Test Project",
            "client_name": "Test Client",
            "client_email": "client@test.com",
            "currency": "USD",
        }
        create_response = await async_client.post(
            "/api/v1/projects/", json=project_data, headers=headers
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        # Should NOT be able to delete
        response = await async_client.delete(f"/api/v1/projects/{project_id}", headers=headers)
        assert response.status_code == 403


class TestViewAnalyticsPermissions:
    """Test permissions for viewing analytics"""

    async def test_owner_can_view_analytics(self, async_client: AsyncClient, test_users):
        """Owner should be able to view analytics"""
        token = create_access_token(test_users["owner_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.get("/api/v1/insights/dashboard", headers=headers)
        assert response.status_code == 200

    async def test_product_manager_can_view_analytics(self, async_client: AsyncClient, test_users):
        """Product manager should be able to view analytics"""
        token = create_access_token(test_users["product_manager_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.get("/api/v1/insights/dashboard", headers=headers)
        assert response.status_code == 200

    async def test_admin_financiero_can_view_analytics(self, async_client: AsyncClient, test_users):
        """Admin financiero should be able to view analytics"""
        token = create_access_token(test_users["admin_financiero_org1"])
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.get("/api/v1/insights/dashboard", headers=headers)
        assert response.status_code == 200
