"""
Contract tests for operational cost dashboard endpoint.
Freezes payload keys/types so frontend integration remains stable.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.organization import Organization
from app.models.user import User


def _auth_headers(user: User) -> dict:
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "organization_id": user.organization_id,
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def owner_user_for_operational_contract(db_session: AsyncSession) -> User:
    org = Organization(
        name=f"Operational Contract Org {uuid.uuid4().hex[:6]}",
        slug=f"operational-contract-org-{uuid.uuid4().hex[:8]}",
        subscription_plan="free",
        subscription_status="active",
    )
    db_session.add(org)
    await db_session.flush()
    user = User(
        email=f"op-contract-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Operational Contract Owner",
        role="owner",
        role_type="tenant",
        hashed_password=get_password_hash("password123"),
        organization_id=org.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.integration
class TestOperationalCostContract:
    async def test_operational_cost_response_contract(
        self,
        async_client: AsyncClient,
        owner_user_for_operational_contract: User,
    ):
        response = await async_client.get(
            "/api/v1/dashboard/operational-costs?period=current_month",
            headers=_auth_headers(owner_user_for_operational_contract),
        )
        assert response.status_code == 200
        payload = response.json()

        required_keys = [
            "resource_costs",
            "fixed_costs",
            "amortization",
            "tax_costs",
            "total_operational_cost",
            "target_margin_configured",
            "effective_margin_observed",
            "calculation_metadata",
            "data_integrity_ok",
        ]
        for key in required_keys:
            assert key in payload, f"Missing key: {key}"

        assert isinstance(payload["resource_costs"], str)
        assert isinstance(payload["fixed_costs"], str)
        assert isinstance(payload["amortization"], str)
        assert isinstance(payload["tax_costs"], str)
        assert isinstance(payload["total_operational_cost"], str)
        assert payload["target_margin_configured"] is None or isinstance(
            payload["target_margin_configured"], str
        )
        assert payload["effective_margin_observed"] is None or isinstance(
            payload["effective_margin_observed"], str
        )
        assert isinstance(payload["data_integrity_ok"], bool)

        metadata = payload["calculation_metadata"]
        metadata_keys = [
            "currency",
            "period_start",
            "period_end",
            "formula_version",
            "calculation_id",
        ]
        for key in metadata_keys:
            assert key in metadata, f"Missing metadata key: {key}"
        assert isinstance(metadata["currency"], str)
        assert isinstance(metadata["period_start"], str)
        assert isinstance(metadata["period_end"], str)
        assert isinstance(metadata["formula_version"], str)
        assert metadata["calculation_id"] is None or isinstance(metadata["calculation_id"], str)
