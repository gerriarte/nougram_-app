"""
Baseline contract and smoke tests for credits, projects, quotes, onboarding, and settings.

These tests freeze the current API contract (response shapes and status codes) so that
refactors (endpoint -> service -> repository) can be validated without changing behavior.
Run these before and after each phase to ensure no regressions.
"""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.organization import Organization
from app.models.user import User
from app.services.credit_service import CreditService


def _auth_headers(user: User) -> dict:
    """Generate authorization headers for contract tests (token must include sub and organization_id)."""
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "name": getattr(user, "full_name", None),
        "organization_id": user.organization_id,
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


# --- Fixtures (tenant user with org for credits/projects/onboarding/settings) ---


@pytest.fixture
async def tenant_user(db_session: AsyncSession, test_organization: Organization) -> User:
    """Create a tenant user for contract tests (has organization_id, role_type=tenant)."""
    user = User(
        email=f"contract-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Contract Test User",
        role="owner",
        role_type="tenant",
        hashed_password=get_password_hash("password123"),
        organization_id=test_organization.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# --- Credits contract ---

CREDIT_BALANCE_REQUIRED_KEYS = [
    "organization_id",
    "credits_available",
    "credits_used_total",
    "credits_used_this_month",
    "credits_per_month",
    "manual_credits_bonus",
    "last_reset_at",
    "next_reset_at",
    "is_unlimited",
]


@pytest.mark.integration
class TestCreditsContract:
    """Contract tests for GET /api/v1/credits/me/balance and /me/history."""

    async def test_credits_me_balance_contract(
        self,
        async_client: AsyncClient,
        tenant_user: User,
    ):
        """GET /api/v1/credits/me/balance returns 200 and CreditBalanceResponse shape."""
        response = await async_client.get(
            "/api/v1/credits/me/balance",
            headers=_auth_headers(tenant_user),
        )
        assert response.status_code == 200
        payload = response.json()
        for key in CREDIT_BALANCE_REQUIRED_KEYS:
            assert key in payload, f"Missing contract key: {key}"
        assert isinstance(payload["organization_id"], int)
        assert isinstance(payload["credits_available"], int)
        assert isinstance(payload["credits_used_total"], int)
        assert isinstance(payload["credits_used_this_month"], int)
        assert isinstance(payload["is_unlimited"], bool)
        assert payload.get("credits_per_month") is None or isinstance(payload["credits_per_month"], int)
        assert payload.get("last_reset_at") is None or isinstance(payload["last_reset_at"], str)
        assert payload.get("next_reset_at") is None or isinstance(payload["next_reset_at"], str)

    async def test_credits_me_history_contract(
        self,
        async_client: AsyncClient,
        tenant_user: User,
    ):
        """GET /api/v1/credits/me/history returns 200 and paginated list shape."""
        response = await async_client.get(
            "/api/v1/credits/me/history?page=1&page_size=5",
            headers=_auth_headers(tenant_user),
        )
        assert response.status_code == 200
        payload = response.json()
        assert "items" in payload
        assert "total" in payload
        assert "page" in payload
        assert "page_size" in payload
        assert "total_pages" in payload
        assert isinstance(payload["items"], list)
        assert isinstance(payload["total"], int)
        assert isinstance(payload["page"], int)
        assert isinstance(payload["page_size"], int)
        assert isinstance(payload["total_pages"], int)


# --- Projects/quotes contract and smoke ---


@pytest.mark.integration
class TestProjectQuoteContract:
    """Contract and smoke tests for POST /api/v1/projects/ (create project with quote)."""

    async def test_create_project_with_quote_contract(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        tenant_user: User,
        test_organization: Organization,
        test_service,
        test_settings,
        test_team_member,
    ):
        """POST /api/v1/projects/ with quote_items returns 201 and QuoteResponseWithItems shape."""
        await CreditService.grant_subscription_credits(test_organization.id, db_session, force=True)
        response = await async_client.post(
            "/api/v1/projects/",
            json={
                "name": "Contract Test Project",
                "client_name": "Contract Client",
                "client_email": "contract@example.com",
                "currency": "USD",
                "quote_items": [{"service_id": test_service.id, "estimated_hours": 10.0}],
                "tax_ids": [],
            },
            headers=_auth_headers(tenant_user),
        )
        assert response.status_code == 201
        payload = response.json()
        assert "project_id" in payload
        assert "id" in payload  # quote id
        assert "items" in payload
        assert "version" in payload
        assert isinstance(payload["project_id"], int)
        assert isinstance(payload["id"], int)
        assert isinstance(payload["items"], list)

    async def test_create_project_with_quote_consumes_one_credit(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        tenant_user: User,
        test_organization: Organization,
        test_service,
        test_settings,
        test_team_member,
    ):
        """Smoke: creating a project with initial quote consumes exactly 1 credit."""
        await CreditService.grant_subscription_credits(test_organization.id, db_session, force=True)
        before = await CreditService.get_credit_balance(test_organization.id, db_session)
        await async_client.post(
            "/api/v1/projects/",
            json={
                "name": "Credit Smoke Project",
                "client_name": "Smoke Client",
                "client_email": "smoke@example.com",
                "currency": "USD",
                "quote_items": [{"service_id": test_service.id, "estimated_hours": 5.0}],
                "tax_ids": [],
            },
            headers=_auth_headers(tenant_user),
        )
        after = await CreditService.get_credit_balance(test_organization.id, db_session)
        assert before["credits_available"] - after["credits_available"] == 1

    async def test_create_project_returns_402_when_no_credits(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        tenant_user: User,
        test_organization: Organization,
        test_service,
        test_settings,
        test_team_member,
    ):
        """Creating a quote returns 402 when organization has no available credits."""
        await CreditService.grant_subscription_credits(test_organization.id, db_session, force=True)
        balance = await CreditService.get_credit_balance(test_organization.id, db_session)
        if balance["credits_available"] > 0:
            await CreditService.validate_and_consume_credits(
                organization_id=test_organization.id,
                amount=balance["credits_available"],
                user_id=tenant_user.id,
                reason="Contract test: exhaust credits",
                db=db_session,
            )
        response = await async_client.post(
            "/api/v1/projects/",
            json={
                "name": "No Credit Project",
                "client_name": "No Credit Client",
                "client_email": "nocredit@example.com",
                "currency": "USD",
                "quote_items": [{"service_id": test_service.id, "estimated_hours": 6.0}],
                "tax_ids": [],
            },
            headers=_auth_headers(tenant_user),
        )
        assert response.status_code == 402


# --- Onboarding contract ---

BENCHMARKS_RESPONSE_KEYS = ["profile_type", "country", "currency", "benchmarks", "source"]
BENCHMARK_KEYS = [
    "avg_monthly_income", "avg_margin", "avg_hours_per_month",
    "avg_team_size", "avg_salary", "avg_clients",
]


@pytest.mark.integration
class TestOnboardingContract:
    """Contract tests for GET /api/v1/onboarding/benchmarks."""

    async def test_onboarding_benchmarks_contract(
        self,
        async_client: AsyncClient,
        tenant_user: User,
    ):
        """GET /api/v1/onboarding/benchmarks returns 200 and BenchmarksResponse shape."""
        response = await async_client.get(
            "/api/v1/onboarding/benchmarks?profile_type=freelance&country=US&currency=USD",
            headers=_auth_headers(tenant_user),
        )
        assert response.status_code == 200
        payload = response.json()
        for key in BENCHMARKS_RESPONSE_KEYS:
            assert key in payload, f"Missing key: {key}"
        benchmarks = payload.get("benchmarks")
        assert benchmarks is not None
        for key in BENCHMARK_KEYS:
            assert key in benchmarks, f"Missing benchmarks key: {key}"


# --- Settings contract ---

SETTINGS_CURRENCY_KEYS = ["primary_currency", "currency_symbol", "available_currencies", "exchange_rates"]


@pytest.mark.integration
class TestSettingsContract:
    """Contract tests for GET /api/v1/settings/currency."""

    async def test_settings_currency_contract(
        self,
        async_client: AsyncClient,
        tenant_user: User,
    ):
        """GET /api/v1/settings/currency returns 200 and AgencySettingsResponse shape."""
        response = await async_client.get(
            "/api/v1/settings/currency",
            headers=_auth_headers(tenant_user),
        )
        assert response.status_code == 200
        payload = response.json()
        for key in SETTINGS_CURRENCY_KEYS:
            assert key in payload, f"Missing key: {key}"
        assert isinstance(payload["primary_currency"], str)
        assert isinstance(payload["currency_symbol"], str)
        assert isinstance(payload["available_currencies"], list)
