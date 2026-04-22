"""
CreditTransaction model for tracking credit transactions
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class CreditTransaction(Base):
    """
    CreditTransaction model for tracking all credit transactions

    Records every credit transaction:
    - Subscription grants (monthly allocation)
    - Manual adjustments (admin grants)
    - Consumption (using credits)
    - Refunds (returning credits)
    """

    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Transaction details
    transaction_type = Column(
        String(32), nullable=False, index=True
    )  # subscription_grant, manual_adjustment, consumption, refund
    amount = Column(Integer, nullable=False)  # Positive = added, negative = consumed

    # Context
    reason = Column(Text, nullable=True)  # Human-readable reason
    reference_id = Column(Integer, nullable=True)  # ID of related quote/project

    # Who performed the transaction
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamp
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    organization = relationship("Organization")
    user = relationship("User", foreign_keys=[performed_by])
