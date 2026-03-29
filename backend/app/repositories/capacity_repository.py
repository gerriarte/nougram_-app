"""
Repository for capacity commitments/events and quote loading for occupancy sync.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import delete, select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
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
        if not commitments:
            return

        bind = self.db.get_bind()
        dialect_name = bind.dialect.name if bind is not None else None

        # PostgreSQL path: upsert to be resilient to retries/concurrency.
        if dialect_name == "postgresql":
            rows: list[dict] = []
            for commitment in commitments:
                rows.append(
                    {
                        "organization_id": commitment.organization_id,
                        "team_member_id": commitment.team_member_id,
                        "cell_id": commitment.cell_id,
                        "source_type": commitment.source_type,
                        "source_id": commitment.source_id,
                        "state": commitment.state,
                        "period_start": commitment.period_start,
                        "period_end": commitment.period_end,
                        "hours": commitment.hours,
                    }
                )

            stmt = pg_insert(CapacityCommitment).values(rows)
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=[
                    CapacityCommitment.organization_id,
                    CapacityCommitment.team_member_id,
                    CapacityCommitment.source_type,
                    CapacityCommitment.source_id,
                    CapacityCommitment.state,
                    CapacityCommitment.period_start,
                    CapacityCommitment.period_end,
                ],
                set_={
                    "hours": stmt.excluded.hours,
                    "cell_id": func.coalesce(stmt.excluded.cell_id, CapacityCommitment.cell_id),
                    "updated_at": func.now(),
                },
            )
            await self.db.execute(upsert_stmt)
            return

        # SQLite/tests fallback
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
