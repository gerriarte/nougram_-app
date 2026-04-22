"""
DISABLED DURING ROLLBACK
This file is a placeholder to prevent import errors
"""

import enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import Base


class UserRole(enum.StrEnum):
    """Disabled enum - placeholder only"""

    SUPER_ADMIN = "super_admin"
    ADMIN_FINANCIERO = "admin_financiero"
    PRODUCT_MANAGER = "product_manager"


class DeleteRequestStatus(enum.StrEnum):
    """Disabled enum - placeholder only"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DeleteRequest(Base):
    """Disabled model - placeholder only"""

    __tablename__ = "delete_requests"

    id = Column(Integer, primary_key=True, index=True)
    resource_type = Column(String, nullable=False)
    resource_id = Column(Integer, nullable=False)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    requested_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
