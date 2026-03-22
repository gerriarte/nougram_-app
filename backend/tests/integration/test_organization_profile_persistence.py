"""
Integration test: organization profile fields persist in DB settings.
"""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.organization import Organization
from app.models.user import User


def _auth_headers(user: User) -> dict:
    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "organization_id": user.organization_id,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def org_profile_org(db_session: AsyncSession) -> Organization:
    org = Organization(
        name="Profile Persistence Org",
        slug=f"profile-persist-{uuid.uuid4().hex[:8]}",
        subscription_plan="starter",
        subscription_status="active",
        settings={},
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def org_profile_owner(db_session: AsyncSession, org_profile_org: Organization) -> User:
    user = User(
        email=f"owner-profile-{uuid.uuid4().hex[:8]}@test.com",
        full_name="Owner Profile",
        hashed_password=get_password_hash("test123"),
        role="owner",
        role_type="tenant",
        organization_id=org_profile_org.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.integration
async def test_company_profile_fields_persist_in_org_settings(
    async_client: AsyncClient,
    org_profile_org: Organization,
    org_profile_owner: User,
):
    payload = {
        "name": "Acme Labs S.A.S.",
        "settings": {
            "nit": "900123456-7",
            "employee_count": 57,
            "origin_country": "Colombia",
            "origin_city": "Bogotá",
        },
    }

    update_response = await async_client.put(
        f"/api/v1/organizations/{org_profile_org.id}",
        json=payload,
        headers=_auth_headers(org_profile_owner),
    )
    assert update_response.status_code == 200
    updated = update_response.json()

    assert updated["name"] == "Acme Labs S.A.S."
    assert updated["settings"]["nit"] == "900123456-7"
    assert updated["settings"]["employee_count"] == 57
    assert updated["settings"]["origin_country"] == "Colombia"
    assert updated["settings"]["origin_city"] == "Bogotá"

    me_response = await async_client.get(
        "/api/v1/organizations/me",
        headers=_auth_headers(org_profile_owner),
    )
    assert me_response.status_code == 200
    me = me_response.json()

    assert me["name"] == "Acme Labs S.A.S."
    assert me["settings"]["nit"] == "900123456-7"
    assert me["settings"]["employee_count"] == 57
    assert me["settings"]["origin_country"] == "Colombia"
    assert me["settings"]["origin_city"] == "Bogotá"
