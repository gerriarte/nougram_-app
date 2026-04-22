"""
Audit Log model for tracking critical actions in the system
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AuditLog(Base):
    """
    Audit log for tracking critical user actions and system events

    Logs actions such as:
    - User authentication (login, logout)
    - Data modifications (create, update, delete)
    - Access to sensitive data
    - Permission changes
    - Subscription changes
    - Security events
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # User and organization context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)

    # Action details
    action = Column(
        String(100), nullable=False, index=True
    )  # e.g., "user.login", "project.create", "subscription.update"
    resource_type = Column(
        String(50), nullable=True, index=True
    )  # e.g., "project", "user", "subscription"
    resource_id = Column(Integer, nullable=True, index=True)  # ID of the affected resource

    # Action metadata
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)  # Browser/client user agent
    details = Column(Text, nullable=True)  # JSON or text details about the action

    # Status
    status = Column(
        String(20), nullable=False, default="success", index=True
    )  # success, failure, error
    error_message = Column(Text, nullable=True)  # Error message if status is failure/error

    # Timestamp
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    organization = relationship("Organization", foreign_keys=[organization_id])

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id}, created_at={self.created_at})>"
