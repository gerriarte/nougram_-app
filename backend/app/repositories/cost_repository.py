"""
Repository for CostFixed model
"""

from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cost import CostFixed
from app.repositories.base import BaseRepository


class CostRepository(BaseRepository[CostFixed]):
    """
    Repository for CostFixed operations
    """

    def __init__(self, db: AsyncSession, tenant_id: int | None = None):
        super().__init__(db, CostFixed, tenant_id=tenant_id)

    async def get_all_active(self, include_deleted: bool = False) -> list[CostFixed]:
        """
        Get all active costs ordered by creation date

        Args:
            include_deleted: Whether to include soft-deleted costs

        Returns:
            List of CostFixed instances
        """
        return await self.get_all(
            include_deleted=include_deleted, order_by=desc(CostFixed.created_at)
        )

    async def get_by_category(
        self, category: str, include_deleted: bool = False
    ) -> list[CostFixed]:
        """
        Get costs by category

        Args:
            category: Cost category
            include_deleted: Whether to include soft-deleted costs

        Returns:
            List of CostFixed instances
        """
        return await self.get_all(
            where=CostFixed.category == category, include_deleted=include_deleted
        )
