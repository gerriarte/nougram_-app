"""
Integration tests for invitation endpoints
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.organization import Organization
from app.models.user import User


def get_auth_headers(user: User) -> dict:
    """Generate authorization headers for a user"""
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.full_name,
        "organization_id": user.organization_id,
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestInvitationEndpoints:
    """Tests for invitation endpoints"""

    @pytest.mark.asyncio
    async def test_create_invitation_success(
        self, async_client: AsyncClient, test_admin_user: User, test_organization: Organization
    ):
        """Test successful invitation creation"""
        headers = get_auth_headers(test_admin_user)
        response = await async_client.post(
            f"/api/v1/organizations/{test_organization.id}/invitations",
            json={"email": "newuser@example.com", "role": "user"},
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"
        assert data["organization_id"] == test_organization.id
        assert data["status"] == "pending"
        assert "expires_at" in data

    @pytest.mark.asyncio
    async def test_create_invitation_duplicate_email(
        self,
        async_client: AsyncClient,
        test_admin_user: User,
        test_organization: Organization,
        test_user: User,
    ):
        """Test creating invitation for user already in organization"""
        headers = get_auth_headers(test_admin_user)
        response = await async_client.post(
            f"/api/v1/organizations/{test_organization.id}/invitations",
            json={"email": test_user.email, "role": "user"},
            headers=headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert "already a member" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_invitation_duplicate_pending(
        self,
        async_client: AsyncClient,
        test_admin_user: User,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test creating duplicate pending invitation"""
        from app.repositories.invitation_repository import InvitationRepository

        # Create first invitation
        invitation_repo = InvitationRepository(db_session, tenant_id=test_organization.id)
        await invitation_repo.create_invitation(
            organization_id=test_organization.id,
            email="duplicate@example.com",
            role="user",
            token="test-token-1",
            expires_at=datetime.now(UTC) + timedelta(days=7),
            created_by_id=test_admin_user.id,
        )
        await db_session.commit()

        # Try to create duplicate
        headers = get_auth_headers(test_admin_user)
        response = await async_client.post(
            f"/api/v1/organizations/{test_organization.id}/invitations",
            json={"email": "duplicate@example.com", "role": "user"},
            headers=headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert "pending invitation" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_invitation_no_permission(
        self, async_client: AsyncClient, test_user: User, test_organization: Organization
    ):
        """Test creating invitation without permission"""
        headers = get_auth_headers(test_user)
        response = await async_client.post(
            f"/api/v1/organizations/{test_organization.id}/invitations",
            json={"email": "newuser@example.com", "role": "user"},
            headers=headers,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_invitations_success(
        self,
        async_client: AsyncClient,
        test_admin_user: User,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test listing invitations"""
        from app.repositories.invitation_repository import InvitationRepository

        # Create test invitations
        invitation_repo = InvitationRepository(db_session, tenant_id=test_organization.id)
        await invitation_repo.create_invitation(
            organization_id=test_organization.id,
            email="invite1@example.com",
            role="user",
            token="token-1",
            expires_at=datetime.now(UTC) + timedelta(days=7),
            created_by_id=test_admin_user.id,
        )
        await invitation_repo.create_invitation(
            organization_id=test_organization.id,
            email="invite2@example.com",
            role="org_admin",
            token="token-2",
            expires_at=datetime.now(UTC) + timedelta(days=7),
            created_by_id=test_admin_user.id,
        )
        await db_session.commit()

        headers = get_auth_headers(test_admin_user)
        response = await async_client.get(
            f"/api/v1/organizations/{test_organization.id}/invitations", headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2
        # Verify tokens are not exposed
        for item in data["items"]:
            assert item["token"] == ""

    @pytest.mark.asyncio
    async def test_list_invitations_filter_by_status(
        self,
        async_client: AsyncClient,
        test_admin_user: User,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test listing invitations filtered by status"""
        from app.repositories.invitation_repository import InvitationRepository

        # Create pending invitation
        invitation_repo = InvitationRepository(db_session, tenant_id=test_organization.id)
        await invitation_repo.create_invitation(
            organization_id=test_organization.id,
            email="pending@example.com",
            role="user",
            token="token-pending",
            expires_at=datetime.now(UTC) + timedelta(days=7),
            created_by_id=test_admin_user.id,
        )
        await db_session.commit()

        headers = get_auth_headers(test_admin_user)
        response = await async_client.get(
            f"/api/v1/organizations/{test_organization.id}/invitations?status=pending",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert all(item["status"] == "pending" for item in data["items"])

    @pytest.mark.asyncio
    async def test_cancel_invitation_success(
        self,
        async_client: AsyncClient,
        test_admin_user: User,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test canceling an invitation"""
        from app.repositories.invitation_repository import InvitationRepository

        # Create invitation
        invitation_repo = InvitationRepository(db_session, tenant_id=test_organization.id)
        invitation = await invitation_repo.create_invitation(
            organization_id=test_organization.id,
            email="tocancel@example.com",
            role="user",
            token="token-cancel",
            expires_at=datetime.now(UTC) + timedelta(days=7),
            created_by_id=test_admin_user.id,
        )
        await db_session.commit()

        headers = get_auth_headers(test_admin_user)
        response = await async_client.delete(
            f"/api/v1/organizations/{test_organization.id}/invitations/{invitation.id}",
            headers=headers,
        )

        assert response.status_code == 204

        # Verify invitation is cancelled
        await db_session.refresh(invitation)
        assert invitation.status == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_invitation_not_found(
        self, async_client: AsyncClient, test_admin_user: User, test_organization: Organization
    ):
        """Test canceling non-existent invitation"""
        headers = get_auth_headers(test_admin_user)
        response = await async_client.delete(
            f"/api/v1/organizations/{test_organization.id}/invitations/99999", headers=headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_validate_invitation_token_success(
        self,
        async_client: AsyncClient,
        test_admin_user: User,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test validating invitation token"""
        from app.repositories.invitation_repository import InvitationRepository

        # Create invitation
        invitation_repo = InvitationRepository(db_session, tenant_id=test_organization.id)
        await invitation_repo.create_invitation(
            organization_id=test_organization.id,
            email="validate@example.com",
            role="user",
            token="validate-token-123",
            expires_at=datetime.now(UTC) + timedelta(days=7),
            created_by_id=test_admin_user.id,
        )
        await db_session.commit()

        # Validate token (public endpoint, no auth required)
        response = await async_client.get(
            "/api/v1/organizations/invitations/validate/validate-token-123"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "validate@example.com"
        assert data["organization_id"] == test_organization.id
        assert data["status"] == "pending"
        # Token should not be exposed
        assert data["token"] == ""

    @pytest.mark.asyncio
    async def test_validate_invitation_token_invalid(self, async_client: AsyncClient):
        """Test validating invalid token"""
        response = await async_client.get(
            "/api/v1/organizations/invitations/validate/invalid-token"
        )

        assert response.status_code == 404
        data = response.json()
        assert "invalid" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_validate_invitation_token_expired(
        self,
        async_client: AsyncClient,
        test_admin_user: User,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test validating expired invitation token"""
        from app.repositories.invitation_repository import InvitationRepository

        # Create expired invitation
        invitation_repo = InvitationRepository(db_session, tenant_id=test_organization.id)
        await invitation_repo.create_invitation(
            organization_id=test_organization.id,
            email="expired@example.com",
            role="user",
            token="expired-token",
            expires_at=datetime.now(UTC) - timedelta(days=1),  # Expired yesterday
            created_by_id=test_admin_user.id,
        )
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/organizations/invitations/validate/expired-token"
        )

        assert response.status_code == 400
        data = response.json()
        assert "expired" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_accept_invitation_new_user(
        self,
        async_client: AsyncClient,
        test_admin_user: User,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test accepting invitation for new user"""
        from app.repositories.invitation_repository import InvitationRepository

        # Create invitation
        invitation_repo = InvitationRepository(db_session, tenant_id=test_organization.id)
        invitation = await invitation_repo.create_invitation(
            organization_id=test_organization.id,
            email="newuser@example.com",
            role="user",
            token="accept-token-new",
            expires_at=datetime.now(UTC) + timedelta(days=7),
            created_by_id=test_admin_user.id,
        )
        await db_session.commit()

        # Accept invitation (public endpoint)
        response = await async_client.post(
            f"/api/v1/organizations/{test_organization.id}/invitations/accept-token-new/accept",
            json={
                "token": "accept-token-new",
                "password": "newpassword123",
                "full_name": "New User",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["organization_id"] == test_organization.id

        # Verify user was created
        result = await db_session.execute(select(User).where(User.email == "newuser@example.com"))
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.organization_id == test_organization.id

        # Verify invitation was marked as accepted
        await db_session.refresh(invitation)
        assert invitation.is_accepted
        assert invitation.accepted_at is not None

    @pytest.mark.asyncio
    async def test_accept_invitation_existing_user(
        self,
        async_client: AsyncClient,
        test_admin_user: User,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test accepting invitation for existing user"""
        from app.repositories.invitation_repository import InvitationRepository

        # Create existing user (not in organization)
        existing_user = User(
            email="existing@example.com",
            full_name="Existing User",
            hashed_password=get_password_hash("existingpassword123"),
            role="user",
            organization_id=None,  # Not in any organization
        )
        db_session.add(existing_user)
        await db_session.commit()

        # Create invitation
        invitation_repo = InvitationRepository(db_session, tenant_id=test_organization.id)
        invitation = await invitation_repo.create_invitation(
            organization_id=test_organization.id,
            email="existing@example.com",
            role="user",
            token="accept-token-existing",
            expires_at=datetime.now(UTC) + timedelta(days=7),
            created_by_id=test_admin_user.id,
        )
        await db_session.commit()

        # Accept invitation (no password needed for existing user)
        response = await async_client.post(
            f"/api/v1/organizations/{test_organization.id}/invitations/accept-token-existing/accept",
            json={"token": "accept-token-existing"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "existing@example.com"

        # Verify user was added to organization
        await db_session.refresh(existing_user)
        assert existing_user.organization_id == test_organization.id

        # Verify invitation was marked as accepted
        await db_session.refresh(invitation)
        assert invitation.is_accepted

    @pytest.mark.asyncio
    async def test_accept_invitation_already_accepted(
        self,
        async_client: AsyncClient,
        test_admin_user: User,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test accepting already accepted invitation"""
        from app.repositories.invitation_repository import InvitationRepository

        # Create and accept invitation
        invitation_repo = InvitationRepository(db_session, tenant_id=test_organization.id)
        invitation = await invitation_repo.create_invitation(
            organization_id=test_organization.id,
            email="accepted@example.com",
            role="user",
            token="already-accepted-token",
            expires_at=datetime.now(UTC) + timedelta(days=7),
            created_by_id=test_admin_user.id,
        )
        # Mark as accepted
        invitation.accepted_at = datetime.now(UTC)
        await db_session.commit()

        # Try to accept again
        response = await async_client.post(
            f"/api/v1/organizations/{test_organization.id}/invitations/already-accepted-token/accept",
            json={
                "token": "already-accepted-token",
                "password": "password123",
                "full_name": "User",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "already been accepted" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_accept_invitation_expired(
        self,
        async_client: AsyncClient,
        test_admin_user: User,
        test_organization: Organization,
        db_session: AsyncSession,
    ):
        """Test accepting expired invitation"""
        from app.repositories.invitation_repository import InvitationRepository

        # Create expired invitation
        invitation_repo = InvitationRepository(db_session, tenant_id=test_organization.id)
        await invitation_repo.create_invitation(
            organization_id=test_organization.id,
            email="expired-accept@example.com",
            role="user",
            token="expired-accept-token",
            expires_at=datetime.now(UTC) - timedelta(days=1),
            created_by_id=test_admin_user.id,
        )
        await db_session.commit()

        # Try to accept
        response = await async_client.post(
            f"/api/v1/organizations/{test_organization.id}/invitations/expired-accept-token/accept",
            json={"token": "expired-accept-token", "password": "password123", "full_name": "User"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "expired" in data["detail"].lower()
