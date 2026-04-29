"""
Repository for proposal documents.
"""

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.proposal import ProposalDocument
from app.repositories.base import BaseRepository


class ProposalRepository(BaseRepository[ProposalDocument]):
    def __init__(self, db: AsyncSession, tenant_id: int | None = None):
        super().__init__(db, ProposalDocument, tenant_id=tenant_id)

    async def get_by_project(self, project_id: int) -> list[ProposalDocument]:
        return await self.get_all(
            where=ProposalDocument.project_id == project_id,
            order_by=desc(ProposalDocument.version),
        )

    async def get_latest_by_project(self, project_id: int) -> ProposalDocument | None:
        query = select(ProposalDocument).where(ProposalDocument.project_id == project_id)
        query = self._apply_tenant_filter(query).order_by(desc(ProposalDocument.version)).limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_for_client_portal(
        self, proposal_id: int, organization_id: int
    ) -> ProposalDocument | None:
        query = (
            select(ProposalDocument)
            .where(
                ProposalDocument.id == proposal_id,
                ProposalDocument.organization_id == organization_id,
            )
            .options(
                selectinload(ProposalDocument.project),
                selectinload(ProposalDocument.organization),
            )
        )
        query = self._apply_tenant_filter(query)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
