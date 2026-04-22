"""
Subscription model for tracking billing and subscription history
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.organization import FlexibleJSON


class Subscription(Base):
    """
    Subscription history and billing information

    Tracks subscription changes, payments, and billing cycles.
    Maintains relationship with Stripe for payment processing.
    """

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Stripe integration
    stripe_subscription_id = Column(String, unique=True, nullable=True, index=True)
    stripe_customer_id = Column(String, nullable=True, index=True)
    stripe_price_id = Column(String, nullable=True)

    # Subscription details
    plan = Column(String, nullable=False, index=True)  # free, starter, professional, enterprise
    status = Column(
        String, nullable=False, index=True
    )  # active, cancelled, past_due, trialing, incomplete, incomplete_expired

    # Billing information
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)

    # Payment information
    latest_invoice_id = Column(String, nullable=True)
    default_payment_method = Column(String, nullable=True)

    # Trial information
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    stripe_metadata = Column(
        FlexibleJSON, nullable=True
    )  # Additional Stripe metadata (renamed from 'metadata' as it's reserved in SQLAlchemy)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="subscriptions")

    def __repr__(self):
        return f"<Subscription(id={self.id}, org_id={self.organization_id}, plan={self.plan}, status={self.status})>"

    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        return self.status in ["active", "trialing"]

    def is_cancelled(self) -> bool:
        """Check if subscription is cancelled"""
        return self.status == "cancelled" or self.cancel_at_period_end is True
