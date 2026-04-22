"""
Repository for Tax model
"""

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tax import Tax
from app.repositories.base import BaseRepository


class TaxRepository(BaseRepository[Tax]):
    """
    Repository for Tax operations
    """

    def __init__(self, db: AsyncSession, tenant_id: int | None = None):
        super().__init__(db, Tax, tenant_id=tenant_id)

    async def get_all_active(self, include_deleted: bool = False) -> list[Tax]:
        """
        Get all active taxes (with tenant scoping)

        Args:
            include_deleted: Whether to include soft-deleted taxes

        Returns:
            List of Tax instances
        """
        query = select(Tax).where(Tax.is_active)

        # Apply tenant filter
        query = self._apply_tenant_filter(query)

        if not include_deleted and hasattr(Tax, "deleted_at"):
            query = query.where(Tax.deleted_at.is_(None))

        query = query.order_by(desc(Tax.created_at))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_code(
        self, code: str, include_deleted: bool = False, exclude_id: int | None = None
    ) -> Tax | None:
        """
        Get tax by code (with tenant scoping)

        Args:
            code: Tax code
            include_deleted: Whether to include soft-deleted taxes
            exclude_id: Optional tax ID to exclude from search (useful for updates)

        Returns:
            Tax instance or None
        """
        query = select(Tax).where(Tax.code == code)

        # Apply tenant filter
        query = self._apply_tenant_filter(query)

        if exclude_id is not None:
            query = query.where(Tax.id != exclude_id)

        if not include_deleted and hasattr(Tax, "deleted_at"):
            query = query.where(Tax.deleted_at.is_(None))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_country(self, country: str, include_deleted: bool = False) -> list[Tax]:
        """
        Get taxes by country

        Args:
            country: Country code
            include_deleted: Whether to include soft-deleted taxes

        Returns:
            List of Tax instances
        """
        return await self.get_all(where=Tax.country == country, include_deleted=include_deleted)
