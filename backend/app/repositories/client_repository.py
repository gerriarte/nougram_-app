"""
Repository for Client model (master catalog, multi-tenant).
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func, desc

from app.repositories.base import BaseRepository
from app.models.client import Client


class ClientRepository(BaseRepository[Client]):
    """Repository for Client operations scoped by organization_id."""

    def __init__(self, db: AsyncSession, tenant_id: Optional[int] = None):
        super().__init__(db, Client, tenant_id=tenant_id)

    async def search(
        self,
        q: str,
        limit: int = 10,
        status_filter: Optional[str] = None,
    ) -> List[Client]:
        """
        Search clients by display_name, requester_name, or email (case-insensitive).
        """
        if not q or len(q.strip()) < 2:
            return []
        limit = min(max(limit, 1), 50)
        pattern = f"%{q.strip().lower()}%"
        query = (
            select(Client)
            .where(Client.organization_id == self.tenant_id)
            .where(
                or_(
                    func.lower(Client.display_name).like(pattern),
                    and_(Client.requester_name.isnot(None), func.lower(Client.requester_name).like(pattern)),
                    and_(Client.email.isnot(None), func.lower(Client.email).like(pattern)),
                )
            )
        )
        if status_filter:
            query = query.where(Client.status == status_filter)
        query = query.order_by(desc(Client.updated_at), desc(Client.id)).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all_paginated(
        self,
        status_filter: Optional[str] = None,
        order_by=None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Client]:
        """List clients with optional filters and pagination."""
        query = select(Client)
        query = self._apply_tenant_filter(query)
        if status_filter:
            query = query.where(Client.status == status_filter)
        if order_by is None:
            order_by = desc(Client.display_name)
        query = query.order_by(order_by)
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())
