"""
Repository for User model
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User operations
    Note: User repository may need special handling for multi-tenant
    Users belong to organizations, but super_admin may need to see all users
    """

    def __init__(self, db: AsyncSession, tenant_id: int | None = None):
        super().__init__(db, User, tenant_id=tenant_id)

    async def get_by_email(self, email: str) -> User | None:
        """
        Get user by email

        Args:
            email: User email

        Returns:
            User instance or None
        """
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_role(self, role: str) -> list[User]:
        """
        Get users by role

        Args:
            role: User role

        Returns:
            List of User instances
        """
        query = select(User).where(User.role == role)
        result = await self.db.execute(query)
        return result.scalars().all()
