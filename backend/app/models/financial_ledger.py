"""
Provider-agnostic financial event ledger for payment lifecycle (manual now, Wompi later).
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class FinancialLedgerEvent(Base):
    __tablename__ = "financial_ledger_events"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    event_type = Column(
        String(64), nullable=False, index=True
    )  # e.g. payment_received, subscription_charged, refund
    provider = Column(
        String(32), nullable=False, default="manual", index=True
    )  # manual, wompi, stripe
    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(
        String(32), nullable=False, default="completed", index=True
    )  # pending, completed, failed, refunded

    external_id = Column(
        String(256), nullable=True, index=True
    )  # provider reference (e.g. Wompi transaction ID)
    reference = Column(String(512), nullable=True)  # human-readable reference
    metadata_json = Column(String(2048), nullable=True)  # optional JSON for provider-specific data

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    organization = relationship("Organization")
