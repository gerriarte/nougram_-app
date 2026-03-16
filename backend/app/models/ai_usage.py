"""
AI usage event model for tracking token consumption and cost per feature (e.g. proposal generation).
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class AIUsageEvent(Base):
    __tablename__ = "ai_usage_events"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposal_documents.id"), nullable=True, index=True)

    feature = Column(String(64), nullable=False, index=True)  # e.g. proposal_ai_generate, proposal_executive_summary
    provider = Column(String(32), nullable=False, default="openai")
    model = Column(String(128), nullable=True)

    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost = Column(Float, nullable=True)  # USD

    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization")
    project = relationship("Project")
    proposal = relationship("ProposalDocument")
    actor = relationship("User", foreign_keys=[actor_user_id])
