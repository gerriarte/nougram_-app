"""
Cost models for fixed costs and overhead
ESTÁNDAR NOUGRAM: Campos monetarios usan Numeric para precisión grado bancario
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class CostFixed(Base):
    """
    Fixed cost model (overhead, subscriptions, etc.)
    ESTÁNDAR NOUGRAM: amount_monthly usa Numeric(19,4) para precisión
    """

    __tablename__ = "costs_fixed"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    amount_monthly = Column(
        Numeric(precision=19, scale=4), nullable=False
    )  # ESTÁNDAR NOUGRAM: Numeric
    currency = Column(String, default="USD", nullable=False)  # USD, COP, ARS, EUR
    category = Column(String, nullable=False)  # 'Overhead', 'Software', etc.
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Soft delete fields
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Multi-tenant: organization relationship
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)

    # Relationships
    deleted_by = relationship("User", foreign_keys=[deleted_by_id])
