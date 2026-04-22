"""
Annual Sales Projection models for Sprint 20
ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal para precisión
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class AnnualSalesProjection(Base):
    """
    Annual sales projection for an organization
    Each organization can have one active projection per year
    """

    __tablename__ = "annual_sales_projections"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)  # Año de la proyección
    is_active = Column(Boolean, default=True)  # Proyección activa (solo una por año)
    notes = Column(String, nullable=True)  # Notas adicionales
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization", backref="annual_sales_projections")
    created_by = relationship("User", backref="created_annual_projections")
    entries = relationship(
        "AnnualSalesProjectionEntry",
        back_populates="projection",
        cascade="all, delete-orphan",
        lazy="selectin",  # Eager load entries
    )

    # Unique constraint: una proyección activa por organización/año
    __table_args__ = (UniqueConstraint("organization_id", "year", name="uq_org_year"),)


class AnnualSalesProjectionEntry(Base):
    """
    Entry in annual sales projection (service/month combination)
    Represents quantity and hours for a specific service in a specific month
    """

    __tablename__ = "annual_sales_projection_entries"

    id = Column(Integer, primary_key=True, index=True)
    projection_id = Column(
        Integer, ForeignKey("annual_sales_projections.id"), nullable=False, index=True
    )
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False, index=True)
    month = Column(Integer, nullable=False)  # 1-12
    quantity = Column(Integer, default=0)  # Cantidad de servicios a vender
    hours_per_unit = Column(Float, default=0.0)  # Horas por unidad de servicio
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    projection = relationship("AnnualSalesProjection", back_populates="entries")
    service = relationship("Service", backref="annual_projection_entries")

    # Unique constraint: una entrada por servicio/mes/proyección
    __table_args__ = (
        UniqueConstraint(
            "projection_id", "service_id", "month", name="uq_projection_service_month"
        ),
    )
