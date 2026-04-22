"""
Repository for Service model
"""

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service
from app.repositories.base import BaseRepository


class ServiceRepository(BaseRepository[Service]):
    """
    Repository for Service operations
    """

    def __init__(self, db: AsyncSession, tenant_id: int | None = None):
        super().__init__(db, Service, tenant_id=tenant_id)

    async def get_all_active(self, include_deleted: bool = False) -> list[Service]:
        """
        Get all active services (with tenant scoping)

        Args:
            include_deleted: Whether to include soft-deleted services

        Returns:
            List of Service instances
        """
        query = select(Service).where(Service.is_active)

        # Apply tenant filter
        query = self._apply_tenant_filter(query)

        if not include_deleted and hasattr(Service, "deleted_at"):
            query = query.where(Service.deleted_at.is_(None))

        query = query.order_by(desc(Service.created_at))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_name(self, name: str, include_deleted: bool = False) -> Service | None:
        """
        Get service by name (with tenant scoping)

        Args:
            name: Service name
            include_deleted: Whether to include soft-deleted services

        Returns:
            Service instance or None
        """
        query = select(Service).where(Service.name == name)

        # Apply tenant filter
        query = self._apply_tenant_filter(query)

        if not include_deleted and hasattr(Service, "deleted_at"):
            query = query.where(Service.deleted_at.is_(None))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()
