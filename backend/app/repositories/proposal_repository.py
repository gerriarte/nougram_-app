"""
Repository for proposal documents.
"""
from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.proposal import ProposalDocument
from app.repositories.base import BaseRepository


class ProposalRepository(BaseRepository[ProposalDocument]):
    def __init__(self, db: AsyncSession, tenant_id: Optional[int] = None):
        super().__init__(db, ProposalDocument, tenant_id=tenant_id)

    async def get_by_project(self, project_id: int) -> List[ProposalDocument]:
        return await self.get_all(
            where=ProposalDocument.project_id == project_id,
            order_by=desc(ProposalDocument.version),
        )

    async def get_latest_by_project(self, project_id: int) -> Optional[ProposalDocument]:
        query = select(ProposalDocument).where(ProposalDocument.project_id == project_id)
        query = self._apply_tenant_filter(query).order_by(desc(ProposalDocument.version)).limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
