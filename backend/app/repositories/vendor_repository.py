"""
Repository for the Vendor catalog model.
"""

from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vendor import Vendor
from app.repositories.base import BaseRepository


class VendorRepository(BaseRepository[Vendor]):
    def __init__(self, db: AsyncSession, tenant_id: int | None = None):
        super().__init__(db, Vendor, tenant_id=tenant_id)

    async def get_all_active(self) -> list[Vendor]:
        return await self.get_all(
            where=Vendor.is_active.is_(True),
            order_by=desc(Vendor.name),
        )

    async def get_by_name(self, name: str, exclude_id: int | None = None) -> Vendor | None:
        from sqlalchemy import select

        query = select(Vendor).where(Vendor.name == name)
        query = self._apply_tenant_filter(query)
        query = query.where(Vendor.deleted_at.is_(None))
        if exclude_id is not None:
            query = query.where(Vendor.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
