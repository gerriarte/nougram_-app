"""
Proposal document model, independent from quote pricing.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.organization import FlexibleJSON


class ProposalDocument(Base):
    __tablename__ = "proposal_documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    title = Column(String, nullable=False)
    body_json = Column(FlexibleJSON, nullable=False, default={})
    status = Column(String, nullable=False, default="draft")  # draft, approved, sent
    is_locked = Column(Integer, nullable=False, default=0)  # 0=False, 1=True for broad DB compatibility
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project")
    organization = relationship("Organization")
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])
