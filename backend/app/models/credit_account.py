"""
CreditAccount model for tracking organization credits
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class CreditAccount(Base):
    """
    CreditAccount model for tracking organization credits

    Each organization has one CreditAccount that tracks:
    - Available credits
    - Total credits used (all time)
    - Credits used this month
    - Credits per month allocation
    - Manual credits bonus
    """

    __tablename__ = "credit_accounts"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer, ForeignKey("organizations.id"), nullable=False, unique=True, index=True
    )

    # Credit balances
    credits_available = Column(Integer, default=0, nullable=False)
    credits_used_total = Column(Integer, default=0, nullable=False)
    credits_used_this_month = Column(Integer, default=0, nullable=False)

    # Monthly allocation (-1 means unlimited)
    credits_per_month = Column(Integer, nullable=True)  # NULL = unlimited

    # Reset tracking
    last_reset_at = Column(DateTime(timezone=True), nullable=True)
    next_reset_at = Column(DateTime(timezone=True), nullable=True)

    # Manual credits bonus
    manual_credits_bonus = Column(Integer, default=0, nullable=False)
    manual_credits_last_assigned_at = Column(DateTime(timezone=True), nullable=True)
    manual_credits_assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="credit_account", uselist=False)
    assigned_by_user = relationship("User", foreign_keys=[manual_credits_assigned_by])
