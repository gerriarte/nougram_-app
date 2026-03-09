"""
Repository for proposal client links (public portal access).
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.proposal import ProposalClientLink
from app.repositories.base import BaseRepository


class ProposalClientLinkRepository(BaseRepository[ProposalClientLink]):
    def __init__(self, db: AsyncSession, tenant_id: Optional[int] = None):
        super().__init__(db, ProposalClientLink, tenant_id=tenant_id)

    async def get_latest_by_proposal(self, proposal_id: int) -> Optional[ProposalClientLink]:
        query = select(ProposalClientLink).where(ProposalClientLink.proposal_id == proposal_id)
        query = self._apply_tenant_filter(query).order_by(desc(ProposalClientLink.id)).limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_by_token(self, token: str) -> Optional[ProposalClientLink]:
        now = datetime.now(timezone.utc)
        query = (
            select(ProposalClientLink)
            .where(
                ProposalClientLink.public_token == token,
                ProposalClientLink.is_active == 1,
                ProposalClientLink.access_expires_at >= now,
            )
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
