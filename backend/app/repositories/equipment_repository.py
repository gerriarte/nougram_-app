"""
Repository for equipment amortization model.
"""
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.equipment import EquipmentAmortization
from app.repositories.base import BaseRepository


class EquipmentRepository(BaseRepository[EquipmentAmortization]):
    def __init__(self, db: AsyncSession, tenant_id: Optional[int] = None):
        super().__init__(db, EquipmentAmortization, tenant_id=tenant_id)

    async def get_all_active(self, include_deleted: bool = False) -> List[EquipmentAmortization]:
        return await self.get_all(
            where=EquipmentAmortization.is_active.is_(True),
            include_deleted=include_deleted,
            order_by=desc(EquipmentAmortization.created_at),
        )
