"""
Billing request model for manual subscription/account actions.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class BillingRequest(Base):
    """
    Request raised by a tenant for manual billing/account actions.
    """

    __tablename__ = "billing_requests"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    requested_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Supported values: change_plan, cancel_subscription, update_payment_method, account_action
    request_type = Column(String(64), nullable=False, index=True)
    target_plan = Column(String(32), nullable=True)
    target_interval = Column(String(16), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="pending", index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    organization = relationship("Organization")
    requested_by_user = relationship("User", foreign_keys=[requested_by_user_id])
