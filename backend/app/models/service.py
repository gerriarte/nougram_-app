"""
Service catalog models
ESTÁNDAR NOUGRAM: Campos monetarios y porcentajes usan Numeric para precisión grado bancario
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Service(Base):
    """
    Service catalog model
    ESTÁNDAR NOUGRAM: Campos monetarios y porcentajes usan Numeric para precisión
    """

    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    default_margin_target = Column(
        Numeric(precision=10, scale=4), default=0.40
    )  # ESTÁNDAR NOUGRAM: Numeric - 40%
    is_active = Column(Boolean, default=True)

    # Pricing type fields (Sprint 14)
    pricing_type = Column(
        String, default="hourly", nullable=False
    )  # "hourly", "fixed", "recurring", "project_value"
    fixed_price = Column(
        Numeric(precision=19, scale=4), nullable=True
    )  # ESTÁNDAR NOUGRAM: Numeric - If pricing_type = "fixed"
    is_recurring = Column(Boolean, default=False)  # If pricing_type = "recurring"
    billing_frequency = Column(String, nullable=True)  # "monthly", "annual" (for recurring)
    recurring_price = Column(
        Numeric(precision=19, scale=4), nullable=True
    )  # ESTÁNDAR NOUGRAM: Numeric - Recurring price (for recurring services)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Soft delete fields
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Multi-tenant: organization relationship
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)

    # Relationships
    deleted_by = relationship("User", foreign_keys=[deleted_by_id])
