"""
Repository for capacity commitments/events and quote loading for occupancy sync.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.capacity import CapacityCommitment, CapacityEvent
from app.models.project import Project, Quote, QuoteItem


class CapacityRepository:
    def __init__(self, db: AsyncSession, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    async def get_quote_for_capacity(self, *, quote_id: int, project_id: int) -> Optional[Quote]:
        query = (
            select(Quote)
            .join(Project, Quote.project_id == Project.id)
            .where(
                Quote.id == quote_id,
                Quote.project_id == project_id,
                Project.organization_id == self.tenant_id,
            )
            .options(
                selectinload(Quote.items).selectinload(QuoteItem.allocations),
                selectinload(Quote.items).selectinload(QuoteItem.cell_assignment),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def delete_commitments_by_source(self, *, source_type: str, source_id: int) -> None:
        await self.db.execute(
            delete(CapacityCommitment).where(
                CapacityCommitment.organization_id == self.tenant_id,
                CapacityCommitment.source_type == source_type,
                CapacityCommitment.source_id == source_id,
            )
        )

    async def add_commitments(self, commitments: list[CapacityCommitment]) -> None:
        if commitments:
            self.db.add_all(commitments)

    async def add_event(
        self,
        *,
        event_type: str,
        source_type: str,
        source_id: int,
        payload: dict,
        created_by_id: Optional[int],
    ) -> CapacityEvent:
        event = CapacityEvent(
            organization_id=self.tenant_id,
            event_type=event_type,
            source_type=source_type,
            source_id=source_id,
            payload=payload,
            created_by_id=created_by_id,
        )
        self.db.add(event)
        return event
