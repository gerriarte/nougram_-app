"""
Repository for team groups/cells and version snapshots.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.team import TeamMember
from app.models.team_cells import TeamCell, TeamCellMemberVersion, TeamCellVersion, TeamGroup


class TeamCellRepository:
    def __init__(self, db: AsyncSession, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    async def list_groups(self, include_inactive: bool = False) -> list[TeamGroup]:
        query = select(TeamGroup).where(TeamGroup.organization_id == self.tenant_id)
        if not include_inactive:
            query = query.where(TeamGroup.is_active == True)
        query = query.order_by(TeamGroup.name.asc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_group(self, group_id: int) -> Optional[TeamGroup]:
        result = await self.db.execute(
            select(TeamGroup).where(
                TeamGroup.id == group_id,
                TeamGroup.organization_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_group(self, *, name: str, description: Optional[str], is_active: bool) -> TeamGroup:
        group = TeamGroup(
            organization_id=self.tenant_id,
            name=name.strip(),
            description=description,
            is_active=is_active,
        )
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def update_group(self, group: TeamGroup) -> TeamGroup:
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def list_cells(self, *, group_id: Optional[int] = None, include_inactive: bool = False) -> list[TeamCell]:
        query = select(TeamCell).where(TeamCell.organization_id == self.tenant_id)
        if group_id is not None:
            query = query.where(TeamCell.group_id == group_id)
        if not include_inactive:
            query = query.where(TeamCell.is_active == True)
        query = query.order_by(TeamCell.name.asc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_cell(self, cell_id: int) -> Optional[TeamCell]:
        result = await self.db.execute(
            select(TeamCell).where(
                TeamCell.id == cell_id,
                TeamCell.organization_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_cell(
        self,
        *,
        group_id: int,
        name: str,
        description: Optional[str],
        is_active: bool,
    ) -> TeamCell:
        cell = TeamCell(
            organization_id=self.tenant_id,
            group_id=group_id,
            name=name.strip(),
            description=description,
            is_active=is_active,
        )
        self.db.add(cell)
        await self.db.commit()
        await self.db.refresh(cell)
        return cell

    async def update_cell(self, cell: TeamCell) -> TeamCell:
        await self.db.commit()
        await self.db.refresh(cell)
        return cell

    async def list_versions(self, cell_id: int) -> list[TeamCellVersion]:
        query = (
            select(TeamCellVersion)
            .where(
                TeamCellVersion.cell_id == cell_id,
                TeamCellVersion.organization_id == self.tenant_id,
            )
            .options(selectinload(TeamCellVersion.members))
            .order_by(TeamCellVersion.version_number.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def validate_members_belong_to_tenant(self, member_ids: list[int]) -> list[TeamMember]:
        if not member_ids:
            return []
        query = (
            select(TeamMember)
            .where(
                TeamMember.id.in_(member_ids),
                TeamMember.organization_id == self.tenant_id,
                TeamMember.is_active == True,
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def publish_version(
        self,
        *,
        cell: TeamCell,
        members_payload: list[dict],
        notes: Optional[str],
        published_by: int,
    ) -> TeamCellVersion:
        # Atomic publish to keep version number and members aligned.
        async with self.db.begin():
            current_max_result = await self.db.execute(
                select(func.max(TeamCellVersion.version_number)).where(TeamCellVersion.cell_id == cell.id)
            )
            current_max = current_max_result.scalar() or 0
            version = TeamCellVersion(
                organization_id=self.tenant_id,
                cell_id=cell.id,
                version_number=current_max + 1,
                status="published",
                notes=notes,
                published_by=published_by,
                published_at=func.now(),
            )
            self.db.add(version)
            await self.db.flush()

            for payload in members_payload:
                self.db.add(
                    TeamCellMemberVersion(
                        organization_id=self.tenant_id,
                        cell_version_id=version.id,
                        team_member_id=payload["team_member_id"],
                        weight=payload.get("weight"),
                        role_override=payload.get("role_override"),
                        is_active=payload.get("is_active", True),
                    )
                )

        result = await self.db.execute(
            select(TeamCellVersion)
            .where(TeamCellVersion.id == version.id)
            .options(selectinload(TeamCellVersion.members))
        )
        return result.scalar_one()
