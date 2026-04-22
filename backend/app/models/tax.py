"""
Tax model for projects
ESTÁNDAR NOUGRAM: Campos de porcentaje usan Numeric para precisión grado bancario
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Tax(Base):
    """
    Tax model - defines taxes that can be applied to projects
    Examples: IVA (Colombia), Transaction Cost (Argentina), VAT (Europe)
    ESTÁNDAR NOUGRAM: percentage usa Numeric(10,4) para precisión
    """

    __tablename__ = "taxes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)  # e.g., "IVA", "Transaction Cost"
    code = Column(String, nullable=False, unique=True, index=True)  # e.g., "IVA_CO", "TX_AR"
    percentage = Column(
        Numeric(precision=10, scale=4), nullable=False, default=0.0
    )  # ESTÁNDAR NOUGRAM: Numeric - Tax percentage (e.g., 19.0 for 19%)
    country = Column(String, nullable=True, index=True)  # Country code (e.g., "CO", "AR", "US")
    is_active = Column(Boolean, default=True)
    description = Column(String, nullable=True)  # Optional description
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Soft delete fields
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Multi-tenant: organization relationship
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)

    # Relationships
    projects = relationship("Project", secondary="project_taxes", back_populates="taxes")
    deleted_by = relationship("User", foreign_keys=[deleted_by_id])
