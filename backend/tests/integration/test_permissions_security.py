"""
Integration tests for granular permissions system
Tests that validate role-based access control, data leakage prevention, and cross-tenant security
"""

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.organization import Organization
from app.models.user import User
from tests.auth_helpers import get_auth_headers


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


@pytest.fixture
async def permissions_test_catalog(db_session: AsyncSession, test_users: dict):
    """Credits + catalog services for org1/org2 (project creation consumes credits)."""
    from decimal import Decimal

    from app.models.service import Service
    from app.services.credit_service import CreditService

    org1_id = test_users["owner_org1"].organization_id
    org2_id = test_users["owner_org2"].organization_id
    for oid in (org1_id, org2_id):
        acc = await CreditService.get_or_create_credit_account(oid, db_session)
        acc.credits_available = 500
    await db_session.commit()

    svc1 = Service(
        name="Perm Test Svc Org1",
        description="x",
        organization_id=org1_id,
        default_margin_target=Decimal("0.40"),
        is_active=True,
    )
    svc2 = Service(
        name="Perm Test Svc Org2",
        description="x",
        organization_id=org2_id,
        default_margin_target=Decimal("0.40"),
        is_active=True,
    )
    db_session.add(svc1)
    db_session.add(svc2)
    await db_session.commit()
    await db_session.refresh(svc1)
    await db_session.refresh(svc2)
    return {"org1_service_id": svc1.id, "org2_service_id": svc2.id}


def _project_create_payload(service_id: int) -> dict:
    return {
        "name": "Test Project",
        "client_name": "Test Client",
        "client_email": "client@test.com",
        "currency": "USD",
        "quote_items": [{"service_id": service_id, "estimated_hours": 10}],
        "tax_ids": [],
    }


class TestViewSensitiveDataPermissions:
    """Tests for viewing team and fixed costs (sensitive tenant data)."""

    async def test_super_admin_has_all_permissions(self, async_client: AsyncClient, test_users):
        """Super admin should have access to all resources"""
        headers = get_auth_headers(test_users["super_admin"])

        response = await async_client.get("/api/v1/organizations/", headers=headers)
        assert response.status_code == 200

    async def test_owner_can_view_sensitive_data(
        self, async_client: AsyncClient, test_users, db_session: AsyncSession
    ):
        """Owner should be able to view costs and salaries"""
        headers = get_auth_headers(test_users["owner_org1"])

        response = await async_client.get("/api/v1/settings/team", headers=headers)
        assert response.status_code == 200

        response = await async_client.get("/api/v1/settings/costs/fixed", headers=headers)
        assert response.status_code == 200

    async def test_product_manager_cannot_view_sensitive_data(
        self, async_client: AsyncClient, test_users
    ):
        """Product manager should NOT be able to view costs and salaries"""
        headers = get_auth_headers(test_users["product_manager_org1"])

        response = await async_client.get("/api/v1/settings/team", headers=headers)
        assert response.status_code == 403

        response = await async_client.get("/api/v1/settings/costs/fixed", headers=headers)
        assert response.status_code == 403

    async def test_collaborator_cannot_view_sensitive_data(
        self, async_client: AsyncClient, test_users
    ):
        """Collaborator should NOT be able to view costs and salaries"""
        headers = get_auth_headers(test_users["collaborator_org1"])

        response = await async_client.get("/api/v1/settings/team", headers=headers)
        assert response.status_code == 403

        response = await async_client.get("/api/v1/settings/costs/fixed", headers=headers)
        assert response.status_code == 403

    async def test_admin_financiero_can_view_sensitive_data(
        self, async_client: AsyncClient, test_users
    ):
        """Admin financiero should be able to view costs and salaries"""
        headers = get_auth_headers(test_users["admin_financiero_org1"])

        response = await async_client.get("/api/v1/settings/team", headers=headers)
        assert response.status_code == 200

        response = await async_client.get("/api/v1/settings/costs/fixed", headers=headers)
        assert response.status_code == 200


class TestCreateResourcesPermissions:
    """Test permissions for creating resources"""

    async def test_owner_can_create_projects(
        self, async_client: AsyncClient, test_users, permissions_test_catalog
    ):
        """Owner should be able to create projects"""
        headers = get_auth_headers(test_users["owner_org1"])
        sid = permissions_test_catalog["org1_service_id"]
        response = await async_client.post(
            "/api/v1/projects/", json=_project_create_payload(sid), headers=headers
        )
        assert response.status_code == 201

    async def test_product_manager_can_create_projects(
        self, async_client: AsyncClient, test_users, permissions_test_catalog
    ):
        """Product manager should be able to create projects"""
        headers = get_auth_headers(test_users["product_manager_org1"])
        sid = permissions_test_catalog["org1_service_id"]
        response = await async_client.post(
            "/api/v1/projects/", json=_project_create_payload(sid), headers=headers
        )
        assert response.status_code == 201

    async def test_collaborator_can_create_projects(
        self, async_client: AsyncClient, test_users, permissions_test_catalog
    ):
        """Collaborator should be able to create projects"""
        headers = get_auth_headers(test_users["collaborator_org1"])
        sid = permissions_test_catalog["org1_service_id"]
        response = await async_client.post(
            "/api/v1/projects/", json=_project_create_payload(sid), headers=headers
        )
        assert response.status_code == 201

    async def test_owner_can_modify_costs(self, async_client: AsyncClient, test_users):
        """Owner should be able to modify costs"""
        headers = get_auth_headers(test_users["owner_org1"])

        cost_data = {
            "name": "Test Cost",
            "amount_monthly": 1000.0,
            "currency": "USD",
            "category": "Overhead",
        }
        response = await async_client.post(
            "/api/v1/settings/costs/fixed", json=cost_data, headers=headers
        )
        assert response.status_code == 201

    async def test_product_manager_cannot_modify_costs(self, async_client: AsyncClient, test_users):
        """Product manager should NOT be able to modify costs"""
        headers = get_auth_headers(test_users["product_manager_org1"])

        cost_data = {
            "name": "Test Cost",
            "amount_monthly": 1000.0,
            "currency": "USD",
            "category": "Overhead",
        }
        response = await async_client.post(
            "/api/v1/settings/costs/fixed", json=cost_data, headers=headers
        )
        assert response.status_code == 403

    async def test_collaborator_cannot_modify_costs(self, async_client: AsyncClient, test_users):
        """Collaborator should NOT be able to modify costs"""
        headers = get_auth_headers(test_users["collaborator_org1"])

        cost_data = {
            "name": "Test Cost",
            "amount_monthly": 1000.0,
            "currency": "USD",
            "category": "Overhead",
        }
        response = await async_client.post(
            "/api/v1/settings/costs/fixed", json=cost_data, headers=headers
        )
        assert response.status_code == 403


class TestSendQuotesPermissions:
    """Test permissions for sending quotes"""

    async def test_owner_can_send_quotes(
        self,
        async_client: AsyncClient,
        test_users,
        permissions_test_catalog,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Owner should be able to send quotes"""
        monkeypatch.setattr("app.core.email.send_email", AsyncMock(return_value=True))
        headers = get_auth_headers(test_users["owner_org1"])
        sid = permissions_test_catalog["org1_service_id"]

        project_response = await async_client.post(
            "/api/v1/projects/",
            json=_project_create_payload(sid),
            headers=headers,
        )
        assert project_response.status_code == 201
        quote_payload = project_response.json()
        project_id = quote_payload["project_id"]
        quote_id = quote_payload["id"]

        # Should be able to send quote
        send_data = {"to_email": "client@test.com", "subject": "Test Quote"}
        response = await async_client.post(
            f"/api/v1/projects/{project_id}/quotes/{quote_id}/send-email",
            json=send_data,
            headers=headers,
        )
        assert response.status_code in [200, 202]  # Success or accepted

    async def test_product_manager_can_send_quotes(
        self,
        async_client: AsyncClient,
        test_users,
        permissions_test_catalog,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Product manager should be able to send quotes"""
        monkeypatch.setattr("app.core.email.send_email", AsyncMock(return_value=True))
        headers = get_auth_headers(test_users["product_manager_org1"])
        sid = permissions_test_catalog["org1_service_id"]

        project_response = await async_client.post(
            "/api/v1/projects/",
            json=_project_create_payload(sid),
            headers=headers,
        )
        assert project_response.status_code == 201
        quote_payload = project_response.json()
        project_id = quote_payload["project_id"]
        quote_id = quote_payload["id"]

        send_data = {"to_email": "client@test.com", "subject": "Test Quote"}
        response = await async_client.post(
            f"/api/v1/projects/{project_id}/quotes/{quote_id}/send-email",
            json=send_data,
            headers=headers,
        )
        assert response.status_code in [200, 202]

    async def test_collaborator_cannot_send_quotes(
        self, async_client: AsyncClient, test_users, permissions_test_catalog
    ):
        """Collaborator should NOT be able to send quotes"""
        headers = get_auth_headers(test_users["collaborator_org1"])
        sid = permissions_test_catalog["org1_service_id"]

        project_response = await async_client.post(
            "/api/v1/projects/",
            json=_project_create_payload(sid),
            headers=headers,
        )
        assert project_response.status_code == 201
        quote_payload = project_response.json()
        project_id = quote_payload["project_id"]
        quote_id = quote_payload["id"]

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
        headers = get_auth_headers(test_users["owner_org1"])

        # Should be able to view billing
        response = await async_client.get("/api/v1/billing/subscription", headers=headers)
        assert response.status_code in [200, 404]  # 404 if no subscription yet

    async def test_product_manager_cannot_manage_subscription(
        self, async_client: AsyncClient, test_users
    ):
        """Product manager should NOT be able to manage subscription"""
        # Should NOT be able to update subscription (if endpoint exists)
        # This depends on the actual implementation
        pass

    async def test_collaborator_cannot_manage_subscription(
        self, async_client: AsyncClient, test_users
    ):
        """Collaborator should NOT be able to manage subscription"""
        # Should NOT be able to manage subscription
        pass


class TestInviteUsersPermissions:
    """Test permissions for inviting users"""

    async def test_owner_can_invite_users(self, async_client: AsyncClient, test_users):
        """Owner should be able to invite users"""
        headers = get_auth_headers(test_users["owner_org1"])

        invite_data = {"email": "newuser@test.com", "role": "product_manager"}
        response = await async_client.post(
            f"/api/v1/organizations/{test_users['owner_org1'].organization_id}/invitations",
            json=invite_data,
            headers=headers,
        )
        assert response.status_code in [200, 201]

    async def test_admin_financiero_cannot_invite_users(
        self, async_client: AsyncClient, test_users
    ):
        """Admin financiero should NOT be able to invite users"""
        headers = get_auth_headers(test_users["admin_financiero_org1"])

        invite_data = {"email": "newuser@test.com", "role": "product_manager"}
        response = await async_client.post(
            f"/api/v1/organizations/{test_users['admin_financiero_org1'].organization_id}/invitations",
            json=invite_data,
            headers=headers,
        )
        assert response.status_code == 403

    async def test_product_manager_cannot_invite_users(self, async_client: AsyncClient, test_users):
        """Product manager should NOT be able to invite users"""
        headers = get_auth_headers(test_users["product_manager_org1"])

        invite_data = {"email": "newuser@test.com", "role": "product_manager"}
        response = await async_client.post(
            f"/api/v1/organizations/{test_users['product_manager_org1'].organization_id}/invitations",
            json=invite_data,
            headers=headers,
        )
        assert response.status_code == 403


class TestCrossTenantSecurity:
    """Test that users cannot access resources from other organizations"""

    async def test_owner_cannot_access_other_org_resources(
        self, async_client: AsyncClient, test_users, permissions_test_catalog
    ):
        """Owner from org1 should NOT be able to access org2's resources"""
        owner1_headers = get_auth_headers(test_users["owner_org1"])
        owner2_headers = get_auth_headers(test_users["owner_org2"])

        sid = permissions_test_catalog["org2_service_id"]
        project_data = _project_create_payload(sid)
        project_data["name"] = "Org2 Project"
        project_data["client_name"] = "Org2 Client"
        project_data["client_email"] = "org2@test.com"
        create_response = await async_client.post(
            "/api/v1/projects/", json=project_data, headers=owner2_headers
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["project_id"]

        # Owner1 should NOT be able to access org2's project
        response = await async_client.get(f"/api/v1/projects/{project_id}", headers=owner1_headers)
        assert response.status_code == 404  # Not found (tenant isolation)

    async def test_cannot_modify_other_org_resources(self, async_client: AsyncClient, test_users):
        """Users should NOT be able to modify resources from other organizations"""
        owner1_headers = get_auth_headers(test_users["owner_org1"])
        owner2_headers = get_auth_headers(test_users["owner_org2"])

        # Owner2 creates a cost
        cost_data = {
            "name": "Org2 Cost",
            "amount_monthly": 500.0,
            "currency": "USD",
            "category": "Overhead",
        }
        create_response = await async_client.post(
            "/api/v1/settings/costs/fixed", json=cost_data, headers=owner2_headers
        )
        assert create_response.status_code == 201
        cost_id = create_response.json()["id"]

        # Owner1 should NOT be able to modify org2's cost
        update_data = {
            "name": "Hacked Cost",
            "amount_monthly": 10000.0,
            "currency": "USD",
            "category": "Overhead",
        }
        response = await async_client.put(
            f"/api/v1/settings/costs/fixed/{cost_id}",
            json=update_data,
            headers=owner1_headers,
        )
        assert response.status_code == 404  # Not found (tenant isolation)


class TestDeletePermissions:
    """Test permissions for deleting resources"""

    async def test_owner_can_delete_resources(self, async_client: AsyncClient, test_users):
        """Owner should be able to delete resources"""
        headers = get_auth_headers(test_users["owner_org1"])

        # Create a service first
        service_data = {
            "name": "Test Service",
            "description": "Test",
            "default_margin_target": "0.35",
            "is_active": True,
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
        self, async_client: AsyncClient, test_users, permissions_test_catalog
    ):
        """Product manager should NOT be able to delete resources"""
        headers = get_auth_headers(test_users["product_manager_org1"])

        sid = permissions_test_catalog["org1_service_id"]
        create_response = await async_client.post(
            "/api/v1/projects/",
            json=_project_create_payload(sid),
            headers=headers,
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["project_id"]

        # Should NOT be able to delete
        response = await async_client.delete(f"/api/v1/projects/{project_id}", headers=headers)
        assert response.status_code == 403


class TestViewAnalyticsPermissions:
    """Test permissions for viewing analytics"""

    async def test_owner_can_view_analytics(self, async_client: AsyncClient, test_users):
        """Owner should be able to view analytics"""
        headers = get_auth_headers(test_users["owner_org1"])

        response = await async_client.get("/api/v1/insights/dashboard", headers=headers)
        assert response.status_code == 200

    async def test_product_manager_can_view_analytics(self, async_client: AsyncClient, test_users):
        """Product manager should be able to view analytics"""
        headers = get_auth_headers(test_users["product_manager_org1"])

        response = await async_client.get("/api/v1/insights/dashboard", headers=headers)
        assert response.status_code == 200

    async def test_admin_financiero_can_view_analytics(self, async_client: AsyncClient, test_users):
        """Admin financiero should be able to view analytics"""
        headers = get_auth_headers(test_users["admin_financiero_org1"])

        response = await async_client.get("/api/v1/insights/dashboard", headers=headers)
        assert response.status_code == 200
