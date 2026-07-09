"""
Quote Agent conversation models.

Persist the chat history between a tenant user and the quote agent, plus the
snapshot of what the agent proposed at confirmation time (for the proposed-vs-final
feedback loop). Tenant-scoped by ``organization_id`` like every other model.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.organization import FlexibleJSON


class AgentConversation(Base):
    """A quote-agent chat session for a tenant user."""

    __tablename__ = "agent_conversations"

    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant scoping (nullable+index, ESTÁNDAR NOUGRAM)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # active | completed | abandoned
    status = Column(String, nullable=False, default="active")

    # Set when the user confirms and a draft Project+Quote is materialized.
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=True, index=True)

    # Frozen copy of the agent's proposal at confirm time (items, hours, engine totals).
    # Enables the proposed-vs-final delta used for feedback / historical grounding.
    proposed_snapshot = Column(FlexibleJSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    messages = relationship(
        "AgentMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AgentMessage.id",
    )


class AgentMessage(Base):
    """A single turn (user/assistant/system/tool) inside a conversation."""

    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer, ForeignKey("agent_conversations.id"), nullable=False, index=True
    )

    # user | assistant | system | tool
    role = Column(String, nullable=False)
    content = Column(Text, nullable=True)

    # Free-form payload: the proposed estimate, tool calls, tool results, etc.
    meta = Column(FlexibleJSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    conversation = relationship("AgentConversation", back_populates="messages")
