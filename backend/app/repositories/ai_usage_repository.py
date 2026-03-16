"""
Repository for AI usage events (token/cost tracking).
No tenant scoping on write; super-admin can query across organizations.
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_usage import AIUsageEvent
from app.repositories.base import BaseRepository


class AIUsageRepository(BaseRepository[AIUsageEvent]):
    def __init__(self, db: AsyncSession, tenant_id: Optional[int] = None):
        super().__init__(db, AIUsageEvent, tenant_id=tenant_id)

    async def create_event(
        self,
        organization_id: int,
        feature: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        estimated_cost: Optional[float] = None,
        model: Optional[str] = None,
        project_id: Optional[int] = None,
        proposal_id: Optional[int] = None,
        actor_user_id: Optional[int] = None,
    ) -> AIUsageEvent:
        entity = AIUsageEvent(
            organization_id=organization_id,
            project_id=project_id,
            proposal_id=proposal_id,
            feature=feature,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            actor_user_id=actor_user_id,
        )
        return await self.create(entity)

    async def list_by_organization(
        self,
        organization_id: int,
        feature: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 500,
        offset: int = 0,
    ) -> List[AIUsageEvent]:
        query = select(AIUsageEvent).where(AIUsageEvent.organization_id == organization_id)
        if feature:
            query = query.where(AIUsageEvent.feature == feature)
        if since is not None:
            query = query.where(AIUsageEvent.created_at >= since)
        if until is not None:
            query = query.where(AIUsageEvent.created_at <= until)
        query = query.order_by(desc(AIUsageEvent.created_at)).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())
