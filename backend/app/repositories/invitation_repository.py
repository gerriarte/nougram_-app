"""
Repository for Invitation model
"""

from datetime import UTC, datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invitation import Invitation
from app.repositories.base import BaseRepository


class InvitationRepository(BaseRepository[Invitation]):
    """Repository for Invitation operations"""

    def __init__(self, db: AsyncSession, tenant_id: int | None = None):
        # Invitations are scoped to organizations (tenant_id = organization_id)
        super().__init__(db, Invitation, tenant_id=tenant_id)

    async def get_by_token(self, token: str) -> Invitation | None:
        """Get invitation by token"""
        query = select(Invitation).where(Invitation.token == token)
        if self.tenant_id:
            query = query.where(Invitation.organization_id == self.tenant_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email_and_org(self, email: str, organization_id: int) -> Invitation | None:
        """Get pending invitation by email and organization"""
        query = select(Invitation).where(
            and_(
                Invitation.email == email,
                Invitation.organization_id == organization_id,
                Invitation.accepted_at.is_(None),  # Only pending invitations
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_by_organization(
        self,
        organization_id: int,
        status: str | None = None,  # "pending", "accepted", "expired"
        include_expired: bool = False,
    ) -> list[Invitation]:
        """
        List invitations for an organization

        Args:
            organization_id: Organization ID
            status: Filter by status (pending, accepted, expired)
            include_expired: Include expired invitations in results

        Returns:
            List of invitations
        """
        query = select(Invitation).where(Invitation.organization_id == organization_id)

        # Filter by status
        if status == "pending":
            query = query.where(
                and_(
                    Invitation.accepted_at.is_(None),
                    Invitation.expires_at > datetime.now(UTC),
                )
            )
        elif status == "accepted":
            query = query.where(Invitation.accepted_at.isnot(None))
        elif status == "expired":
            query = query.where(
                and_(
                    Invitation.accepted_at.is_(None),
                    Invitation.expires_at <= datetime.now(UTC),
                )
            )
        elif not include_expired:
            # By default, exclude expired invitations unless explicitly requested
            query = query.where(
                or_(
                    Invitation.accepted_at.isnot(None),
                    Invitation.expires_at > datetime.now(UTC),
                )
            )

        query = query.order_by(Invitation.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_invitation(
        self,
        organization_id: int,
        email: str,
        role: str,
        token: str,
        expires_at: datetime,
        created_by_id: int,
    ) -> Invitation:
        """
        Create a new invitation

        Args:
            organization_id: Organization ID
            email: Email address to invite
            role: Role to assign when accepted
            token: Unique invitation token
            expires_at: Expiration datetime
            created_by_id: User ID who created the invitation

        Returns:
            Created Invitation instance
        """
        invitation = Invitation(
            organization_id=organization_id,
            email=email,
            role=role,
            token=token,
            expires_at=expires_at,
            created_by_id=created_by_id,
        )
        return await self.create(invitation)

    async def accept_invitation(self, invitation: Invitation) -> Invitation:
        """
        Mark invitation as accepted

        Args:
            invitation: Invitation instance to accept

        Returns:
            Updated Invitation instance
        """
        invitation.accepted_at = datetime.now(UTC)
        return await self.update(invitation)

    async def cancel_invitation(self, invitation_id: int, organization_id: int) -> bool:
        """
        Cancel (delete) a pending invitation

        Args:
            invitation_id: Invitation ID to cancel
            organization_id: Organization ID (for validation)

        Returns:
            True if cancelled, False if not found
        """
        query = select(Invitation).where(
            and_(
                Invitation.id == invitation_id,
                Invitation.organization_id == organization_id,
                Invitation.accepted_at.is_(None),  # Only cancel pending invitations
            )
        )
        result = await self.db.execute(query)
        invitation = result.scalar_one_or_none()

        if invitation:
            await self.delete(invitation)
            return True
        return False

    async def cleanup_expired(self, organization_id: int | None = None) -> int:
        """
        Delete expired invitations (optional cleanup method)

        Args:
            organization_id: Optional organization ID to limit cleanup

        Returns:
            Number of invitations deleted
        """
        query = select(Invitation).where(
            and_(
                Invitation.accepted_at.is_(None),
                Invitation.expires_at <= datetime.now(UTC),
            )
        )

        if organization_id:
            query = query.where(Invitation.organization_id == organization_id)

        result = await self.db.execute(query)
        expired = list(result.scalars().all())

        count = len(expired)
        for invitation in expired:
            await self.delete(invitation)

        return count
