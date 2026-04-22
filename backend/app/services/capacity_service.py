"""
Business service for occupancy commitments derived from proposal decisions.
"""

from __future__ import annotations

import calendar
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.capacity import CapacityCommitment
from app.models.proposal import ProposalClientLink
from app.repositories.factory import RepositoryFactory

logger = get_logger(__name__)


@dataclass
class CapacitySyncResult:
    commitments_count: int
    total_hours: Decimal


class CapacityService:
    def __init__(self, db: AsyncSession, organization_id: int):
        self.db = db
        self.organization_id = organization_id
        self.repo = RepositoryFactory.create_capacity_repository(db, organization_id)

    @staticmethod
    def _month_range(base: datetime, offset: int) -> tuple[datetime, datetime]:
        year = base.year + ((base.month - 1 + offset) // 12)
        month = ((base.month - 1 + offset) % 12) + 1
        _, last_day = calendar.monthrange(year, month)
        start = datetime(year, month, 1, tzinfo=UTC)
        end = datetime(year, month, last_day, 23, 59, 59, tzinfo=UTC)
        return start, end

    @staticmethod
    def _merge_commitments_by_unique_key(
        *,
        organization_id: int,
        source_type: str,
        source_id: int,
        state: str,
        raw_entries: list[tuple[int, int | None, datetime, datetime, Decimal]],
    ) -> list[CapacityCommitment]:
        """
        Merge hours by the same DB unique key to avoid duplicate inserts.
        Unique key in DB excludes cell_id, so we aggregate per member+period.
        """
        aggregated: dict[tuple[int, datetime, datetime], Decimal] = defaultdict(
            lambda: Decimal("0")
        )
        preferred_cell: dict[tuple[int, datetime, datetime], int | None] = {}

        for team_member_id, cell_id, period_start, period_end, hours in raw_entries:
            if hours <= 0:
                continue
            dedup_key = (team_member_id, period_start, period_end)
            aggregated[dedup_key] += hours
            # Preserve first non-null cell for traceability when available.
            if dedup_key not in preferred_cell or preferred_cell[dedup_key] is None:
                preferred_cell[dedup_key] = cell_id

        commitments: list[CapacityCommitment] = []
        for (team_member_id, period_start, period_end), hours in aggregated.items():
            commitments.append(
                CapacityCommitment(
                    organization_id=organization_id,
                    team_member_id=team_member_id,
                    cell_id=preferred_cell.get((team_member_id, period_start, period_end)),
                    source_type=source_type,
                    source_id=source_id,
                    state=state,
                    period_start=period_start,
                    period_end=period_end,
                    hours=hours,
                )
            )
        return commitments

    async def sync_tentative_from_quote(
        self,
        *,
        quote_id: int,
        project_id: int,
        actor_user_id: int | None,
        reference_date: datetime | None = None,
    ) -> CapacitySyncResult:
        await self.repo.delete_commitments_by_source(source_type="quote", source_id=quote_id)

        quote = await self.repo.get_quote_for_capacity(quote_id=quote_id, project_id=project_id)
        if not quote:
            await self.repo.add_event(
                event_type="capacity_commitments_skipped_quote_not_found",
                source_type="quote",
                source_id=quote_id,
                payload={"quote_id": quote_id, "project_id": project_id},
                created_by_id=actor_user_id,
            )
            await self.db.commit()
            return CapacitySyncResult(commitments_count=0, total_hours=Decimal("0"))

        ref_date = reference_date or datetime.now(UTC)
        raw_entries: list[tuple[int, int | None, datetime, datetime, Decimal]] = []
        total_hours = Decimal("0")

        for item in quote.items or []:
            months = 1
            item_cell_id = None
            if getattr(item, "cell_assignment", None) is not None:
                months = max(1, int(getattr(item.cell_assignment, "duration_months", 1) or 1))
                item_cell_id = getattr(item.cell_assignment, "cell_id", None)

            for alloc in item.allocations or []:
                alloc_hours = Decimal(str(alloc.hours or 0))
                if alloc_hours <= 0:
                    continue
                hours_per_month = alloc_hours / Decimal(str(months))
                for offset in range(months):
                    period_start, period_end = self._month_range(ref_date, offset)
                    raw_entries.append(
                        (
                            alloc.team_member_id,
                            item_cell_id,
                            period_start,
                            period_end,
                            hours_per_month,
                        )
                    )
                    total_hours += hours_per_month

        commitments = self._merge_commitments_by_unique_key(
            organization_id=self.organization_id,
            source_type="quote",
            source_id=quote_id,
            state="tentative",
            raw_entries=raw_entries,
        )
        await self.repo.add_commitments(commitments)
        await self.repo.add_event(
            event_type="capacity_commitments_synced",
            source_type="quote",
            source_id=quote_id,
            payload={
                "quote_id": quote_id,
                "project_id": project_id,
                "state": "tentative",
                "commitments_count": len(commitments),
                "total_hours": str(total_hours),
            },
            created_by_id=actor_user_id,
        )
        await self.db.commit()

        logger.info(
            "Tentative capacity commitments synced from quote save",
            organization_id=self.organization_id,
            quote_id=quote_id,
            project_id=project_id,
            commitments_count=len(commitments),
            total_hours=str(total_hours),
        )
        return CapacitySyncResult(commitments_count=len(commitments), total_hours=total_hours)

    async def sync_committed_from_proposal(
        self,
        *,
        link: ProposalClientLink,
        actor_user_id: int | None,
        reference_date: datetime | None = None,
    ) -> CapacitySyncResult:
        await self.repo.delete_commitments_by_source(source_type="proposal_link", source_id=link.id)

        if not link.quote_id:
            await self.repo.add_event(
                event_type="capacity_commitments_skipped_missing_quote",
                source_type="proposal_link",
                source_id=link.id,
                payload={"reason": "missing_quote_id"},
                created_by_id=actor_user_id,
            )
            await self.db.commit()
            return CapacitySyncResult(commitments_count=0, total_hours=Decimal("0"))

        quote = await self.repo.get_quote_for_capacity(
            quote_id=link.quote_id, project_id=link.project_id
        )
        if not quote:
            await self.repo.add_event(
                event_type="capacity_commitments_skipped_quote_not_found",
                source_type="proposal_link",
                source_id=link.id,
                payload={"quote_id": link.quote_id, "project_id": link.project_id},
                created_by_id=actor_user_id,
            )
            await self.db.commit()
            return CapacitySyncResult(commitments_count=0, total_hours=Decimal("0"))

        ref_date = reference_date or datetime.now(UTC)
        raw_entries: list[tuple[int, int | None, datetime, datetime, Decimal]] = []
        total_hours = Decimal("0")

        for item in quote.items or []:
            months = 1
            item_cell_id = None
            if getattr(item, "cell_assignment", None) is not None:
                months = max(1, int(getattr(item.cell_assignment, "duration_months", 1) or 1))
                item_cell_id = getattr(item.cell_assignment, "cell_id", None)

            for alloc in item.allocations or []:
                alloc_hours = Decimal(str(alloc.hours or 0))
                if alloc_hours <= 0:
                    continue
                hours_per_month = alloc_hours / Decimal(str(months))
                for offset in range(months):
                    period_start, period_end = self._month_range(ref_date, offset)
                    raw_entries.append(
                        (
                            alloc.team_member_id,
                            item_cell_id,
                            period_start,
                            period_end,
                            hours_per_month,
                        )
                    )
                    total_hours += hours_per_month

        commitments = self._merge_commitments_by_unique_key(
            organization_id=self.organization_id,
            source_type="proposal_link",
            source_id=link.id,
            state="committed",
            raw_entries=raw_entries,
        )
        await self.repo.add_commitments(commitments)
        await self.repo.add_event(
            event_type="capacity_commitments_synced",
            source_type="proposal_link",
            source_id=link.id,
            payload={
                "quote_id": link.quote_id,
                "project_id": link.project_id,
                "state": "committed",
                "commitments_count": len(commitments),
                "total_hours": str(total_hours),
            },
            created_by_id=actor_user_id,
        )
        await self.db.commit()

        logger.info(
            "Capacity commitments synced from proposal decision",
            organization_id=self.organization_id,
            proposal_link_id=link.id,
            quote_id=link.quote_id,
            commitments_count=len(commitments),
            total_hours=str(total_hours),
        )
        return CapacitySyncResult(commitments_count=len(commitments), total_hours=total_hours)

    async def clear_commitments_for_proposal(
        self,
        *,
        link: ProposalClientLink,
        actor_user_id: int | None,
        reason: str,
    ) -> None:
        await self.repo.delete_commitments_by_source(source_type="proposal_link", source_id=link.id)
        await self.repo.add_event(
            event_type="capacity_commitments_cleared",
            source_type="proposal_link",
            source_id=link.id,
            payload={"reason": reason, "quote_id": link.quote_id, "project_id": link.project_id},
            created_by_id=actor_user_id,
        )
        await self.db.commit()

        logger.info(
            "Capacity commitments cleared from proposal decision",
            organization_id=self.organization_id,
            proposal_link_id=link.id,
            reason=reason,
        )
