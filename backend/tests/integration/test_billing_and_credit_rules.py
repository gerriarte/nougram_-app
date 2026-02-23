"""
Integration tests for billing fallback and quote-credit rules.
"""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.organization import Organization
from app.models.user import User
from app.services.credit_service import CreditService


@pytest.fixture
async def owner_user(db_session: AsyncSession, test_organization: Organization) -> User:
    """Create an owner user for integration rules tests."""
    user = User(
        email=f"owner-rules-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Owner Rules",
        role="owner",
        role_type="tenant",
        hashed_password=get_password_hash("ownerpassword123"),
        organization_id=test_organization.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_financiero_user(db_session: AsyncSession, test_organization: Organization) -> User:
    """Create an admin_financiero user for integration rules tests."""
    user = User(
        email=f"adminfin-rules-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Admin Financiero Rules",
        role="admin_financiero",
        role_type="tenant",
        hashed_password=get_password_hash("adminpassword123"),
        organization_id=test_organization.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def product_manager_user(db_session: AsyncSession, test_organization: Organization) -> User:
    """Create a product_manager user for integration rules tests."""
    user = User(
        email=f"pm-rules-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Product Manager Rules",
        role="product_manager",
        role_type="tenant",
        hashed_password=get_password_hash("pmpassword123"),
        organization_id=test_organization.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def _auth_headers(user: User) -> dict:
    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestOwnerBillingAndCreditsVisibility:
    async def test_owner_gets_subscription_fallback_when_no_subscription_row(
        self,
        async_client: AsyncClient,
        owner_user: User,
        test_organization: Organization,
    ):
        """
        Owner can validate subscription even without active row in subscriptions table.
        """
        response = await async_client.get(
            "/api/v1/billing/subscription",
            headers=_auth_headers(owner_user),
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["organization_id"] == test_organization.id
        assert payload["plan"] == test_organization.subscription_plan
        assert payload["status"] == test_organization.subscription_status

    async def test_owner_can_view_credit_balance(
        self,
        async_client: AsyncClient,
        owner_user: User,
    ):
        """Owner can validate current available credits."""
        response = await async_client.get(
            "/api/v1/credits/me/balance",
            headers=_auth_headers(owner_user),
        )
        assert response.status_code == 200
        payload = response.json()
        assert "credits_available" in payload
        assert "credits_used_this_month" in payload

    async def test_admin_financiero_can_view_subscription_and_credits(
        self,
        async_client: AsyncClient,
        admin_financiero_user: User,
    ):
        """Admin financiero can validate subscription and available credits."""
        subscription_response = await async_client.get(
            "/api/v1/billing/subscription",
            headers=_auth_headers(admin_financiero_user),
        )
        balance_response = await async_client.get(
            "/api/v1/credits/me/balance",
            headers=_auth_headers(admin_financiero_user),
        )
        history_response = await async_client.get(
            "/api/v1/credits/me/history",
            headers=_auth_headers(admin_financiero_user),
        )
        assert subscription_response.status_code == 200
        assert balance_response.status_code == 200
        assert history_response.status_code == 200

    async def test_product_manager_can_view_subscription_and_credits(
        self,
        async_client: AsyncClient,
        product_manager_user: User,
    ):
        """Product manager can validate subscription and available credits."""
        subscription_response = await async_client.get(
            "/api/v1/billing/subscription",
            headers=_auth_headers(product_manager_user),
        )
        balance_response = await async_client.get(
            "/api/v1/credits/me/balance",
            headers=_auth_headers(product_manager_user),
        )
        history_response = await async_client.get(
            "/api/v1/credits/me/history",
            headers=_auth_headers(product_manager_user),
        )
        assert subscription_response.status_code == 200
        assert balance_response.status_code == 200
        assert history_response.status_code == 200


@pytest.mark.integration
class TestQuoteCreditConsumptionRules:
    async def test_quote_creation_consumes_one_credit(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        owner_user: User,
        test_organization: Organization,
        test_service,
        test_settings,
        test_team_member,
    ):
        """
        Creating a project with initial quote consumes exactly 1 credit.
        """
        await CreditService.grant_subscription_credits(test_organization.id, db_session, force=True)
        before = await CreditService.get_credit_balance(test_organization.id, db_session)

        response = await async_client.post(
            "/api/v1/projects/",
            json={
                "name": "Credit Rule Project",
                "client_name": "Client A",
                "client_email": "client-a@example.com",
                "currency": "USD",
                "quote_items": [{"service_id": test_service.id, "estimated_hours": 10.0}],
                "tax_ids": [],
            },
            headers=_auth_headers(owner_user),
        )
        assert response.status_code == 201

        after = await CreditService.get_credit_balance(test_organization.id, db_session)
        assert before["credits_available"] - after["credits_available"] == 1

    async def test_new_quote_version_consumes_one_credit(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        owner_user: User,
        test_organization: Organization,
        test_service,
        test_settings,
        test_team_member,
    ):
        """
        Creating a new quote version consumes exactly 1 additional credit.
        """
        await CreditService.grant_subscription_credits(test_organization.id, db_session, force=True)

        create_response = await async_client.post(
            "/api/v1/projects/",
            json={
                "name": "Versioned Quote Project",
                "client_name": "Client B",
                "client_email": "client-b@example.com",
                "currency": "USD",
                "quote_items": [{"service_id": test_service.id, "estimated_hours": 8.0}],
                "tax_ids": [],
            },
            headers=_auth_headers(owner_user),
        )
        assert create_response.status_code == 201
        created = create_response.json()
        project_id = created["project_id"]
        quote_id = created["id"]

        before = await CreditService.get_credit_balance(test_organization.id, db_session)

        version_response = await async_client.post(
            f"/api/v1/projects/{project_id}/quotes/{quote_id}/new-version",
            json={
                "items": [{"service_id": test_service.id, "estimated_hours": 12.0}],
                "notes": "Version 2",
            },
            headers=_auth_headers(owner_user),
        )
        assert version_response.status_code == 201

        after = await CreditService.get_credit_balance(test_organization.id, db_session)
        assert before["credits_available"] - after["credits_available"] == 1

    async def test_quote_creation_returns_402_when_credits_exhausted(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        owner_user: User,
        test_organization: Organization,
        test_service,
        test_settings,
        test_team_member,
    ):
        """
        Creating a quote returns 402 when organization has no available credits.
        """
        await CreditService.grant_subscription_credits(test_organization.id, db_session, force=True)
        balance = await CreditService.get_credit_balance(test_organization.id, db_session)

        assert balance["is_unlimited"] is False

        # Drain all currently available credits.
        credits_to_consume = int(balance["credits_available"])
        if credits_to_consume > 0:
            await CreditService.validate_and_consume_credits(
                organization_id=test_organization.id,
                amount=credits_to_consume,
                user_id=owner_user.id,
                reason="Test setup: exhaust credits",
                db=db_session,
            )

        empty_balance = await CreditService.get_credit_balance(test_organization.id, db_session)
        assert empty_balance["credits_available"] == 0

        response = await async_client.post(
            "/api/v1/projects/",
            json={
                "name": "No Credit Project",
                "client_name": "Client No Credit",
                "client_email": "nocredit@example.com",
                "currency": "USD",
                "quote_items": [{"service_id": test_service.id, "estimated_hours": 6.0}],
                "tax_ids": [],
            },
            headers=_auth_headers(owner_user),
        )
        assert response.status_code == 402
