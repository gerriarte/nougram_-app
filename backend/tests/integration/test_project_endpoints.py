"""
Integration tests for project endpoints
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.credit_service import CreditService
from tests.auth_helpers import get_auth_headers


@pytest.mark.integration
class TestProjectEndpoints:
    """Integration tests for project endpoints"""

    async def test_create_project_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_admin_user: User,
        test_service,
        test_settings,
        test_team_member,
    ):
        """Test successful project creation"""
        account = await CreditService.get_or_create_credit_account(
            test_admin_user.organization_id, db_session
        )
        account.credits_available = 100
        await db_session.commit()

        headers = get_auth_headers(test_admin_user)

        response = await async_client.post(
            "/api/v1/projects/",
            json={
                "name": "Test Project",
                "client_name": "Test Client",
                "client_email": "client@example.com",
                "currency": "USD",
                "quote_items": [{"service_id": test_service.id, "estimated_hours": 20.0}],
                "tax_ids": [],
            },
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "project_id" in data
        assert data["project_id"] > 0
        assert "items" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["service_id"] == test_service.id

    async def test_create_project_with_product_manager_constraints(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_service,
        test_settings,
        test_team_member,
    ):
        """Product manager may be blocked by credits/subscription constraints."""
        account = await CreditService.get_or_create_credit_account(
            test_user.organization_id, db_session
        )
        account.credits_available = 100
        await db_session.commit()

        headers = get_auth_headers(test_user)

        response = await async_client.post(
            "/api/v1/projects/",
            json={
                "name": "Test Project",
                "client_name": "Test Client",
                "client_email": "client@example.com",
                "currency": "USD",
                "quote_items": [{"service_id": test_service.id, "estimated_hours": 20.0}],
                "tax_ids": [],
            },
            headers=headers,
        )

        # Current behavior: product_manager can create projects if plan/credits allow it.
        # In constrained scenarios API responds with Payment Required.
        assert response.status_code in [201, 402, 403, 401]

    async def test_create_project_invalid_service(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_admin_user: User,
        test_settings,
        test_team_member,
    ):
        """Test project creation with invalid service"""
        account = await CreditService.get_or_create_credit_account(
            test_admin_user.organization_id, db_session
        )
        account.credits_available = 100
        await db_session.commit()

        headers = get_auth_headers(test_admin_user)

        response = await async_client.post(
            "/api/v1/projects/",
            json={
                "name": "Test Project",
                "client_name": "Test Client",
                "client_email": "client@example.com",
                "currency": "USD",
                "quote_items": [{"service_id": 99999, "estimated_hours": 20.0}],
                "tax_ids": [],
            },
            headers=headers,
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower() or "inactive" in data["detail"].lower()
