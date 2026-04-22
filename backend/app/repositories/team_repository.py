"""
Repository for TeamMember model
"""

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import TeamMember
from app.repositories.base import BaseRepository


class TeamRepository(BaseRepository[TeamMember]):
    """
    Repository for TeamMember operations
    """

    def __init__(self, db: AsyncSession, tenant_id: int | None = None):
        super().__init__(db, TeamMember, tenant_id=tenant_id)

    async def get_all_active(self) -> list[TeamMember]:
        """
        Get all active team members (with tenant scoping)

        Returns:
            List of TeamMember instances
        """
        query = select(TeamMember).where(TeamMember.is_active)

        # Apply tenant filter
        query = self._apply_tenant_filter(query)

        query = query.order_by(desc(TeamMember.created_at))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_user_id(self, user_id: int) -> TeamMember | None:
        """
        Get team member by user ID

        Args:
            user_id: User ID

        Returns:
            TeamMember instance or None
        """
        query = select(TeamMember).where(TeamMember.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
