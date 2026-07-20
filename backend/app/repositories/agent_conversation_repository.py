"""
Repository for quote-agent conversations and messages.

Always tenant-scoped by ``organization_id`` through BaseRepository. Messages are
reached through their parent conversation, so message queries validate tenant
ownership by joining on the conversation.
"""

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_conversation import AgentConversation, AgentMessage
from app.repositories.base import BaseRepository


class AgentConversationRepository(BaseRepository[AgentConversation]):
    """Data access for AgentConversation / AgentMessage (tenant-scoped)."""

    def __init__(self, db: AsyncSession, tenant_id: int | None = None):
        super().__init__(db, AgentConversation, tenant_id=tenant_id)

    async def create_conversation(self, user_id: int | None) -> AgentConversation:
        conversation = AgentConversation(
            organization_id=self.tenant_id,
            user_id=user_id,
            status="active",
        )
        return await self.create(conversation)

    async def list_by_organization(
        self, limit: int = 50, offset: int = 0
    ) -> list[AgentConversation]:
        return await self.get_all(
            order_by=desc(AgentConversation.created_at), limit=limit, offset=offset
        )

    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str | None,
        meta: dict | None = None,
    ) -> AgentMessage:
        message = AgentMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            meta=meta,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def list_messages(self, conversation_id: int) -> list[AgentMessage]:
        """Return messages for a conversation the tenant owns (empty if not owned)."""
        conversation = await self.get_by_id(conversation_id)
        if conversation is None:
            return []
        query = (
            select(AgentMessage)
            .where(AgentMessage.conversation_id == conversation_id)
            .order_by(AgentMessage.id)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def set_result(
        self,
        conversation: AgentConversation,
        *,
        project_id: int,
        quote_id: int,
        proposed_snapshot: dict | None,
        status: str = "completed",
    ) -> AgentConversation:
        conversation.project_id = project_id
        conversation.quote_id = quote_id
        conversation.proposed_snapshot = proposed_snapshot
        conversation.status = status
        return await self.update(conversation)
