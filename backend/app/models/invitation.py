"""
Invitation model for organization user invitations
"""

from datetime import UTC

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Invitation(Base):
    """
    Invitation model for inviting users to join organizations

    Tracks invitations sent to users with:
    - Unique token for accepting the invitation
    - Expiration date
    - Status (pending, accepted, expired, cancelled)
    - Role to be assigned upon acceptance
    """

    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, index=True)

    # Organization and user context
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    role = Column(String(32), nullable=False)  # Role to assign when invitation is accepted

    # Invitation token (unique, used for accepting)
    token = Column(String(255), unique=True, nullable=False, index=True)

    # Expiration and acceptance tracking
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    # Who created the invitation
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    organization = relationship("Organization", foreign_keys=[organization_id])
    created_by = relationship("User", foreign_keys=[created_by_id])

    # Composite index for common queries
    __table_args__ = (Index("ix_invitations_org_email", "organization_id", "email"),)

    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired"""
        from datetime import datetime

        if self.expires_at is None:
            return False
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        return exp < datetime.now(UTC)

    @property
    def is_accepted(self) -> bool:
        """Check if invitation has been accepted"""
        return self.accepted_at is not None

    @property
    def status(self) -> str:
        """Get invitation status: pending, accepted, expired, cancelled"""
        if self.is_accepted:
            return "accepted"
        if self.is_expired:
            return "expired"
        return "pending"

    def __repr__(self):
        return f"<Invitation(id={self.id}, email={self.email}, organization_id={self.organization_id}, status={self.status})>"
