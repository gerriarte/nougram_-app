"""
Equipment Amortization Model
NO debe contener queries SQL ni lógica de negocio
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class EquipmentAmortization(Base):
    """
    Equipment Amortization Model

    Modelo para gestionar la amortización de equipos (hardware, software, vehículos, etc.)
    """

    __tablename__ = "equipment_amortization"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Campos básicos
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=False)  # Hardware, Software, Vehicles, Office Equipment

    # Información financiera
    purchase_price = Column(Numeric(15, 2), nullable=False)
    purchase_date = Column(Date, nullable=False)
    currency = Column(String(3), nullable=False)
    exchange_rate_at_purchase = Column(Numeric(10, 4), nullable=True)  # ⚠️ CRÍTICO: TRM histórica

    # Parámetros de depreciación
    useful_life_months = Column(Integer, nullable=False)
    salvage_value = Column(
        Numeric(15, 2), default=0, nullable=False
    )  # ⚠️ CRÍTICO: Valor de salvamento
    depreciation_method = Column(String, nullable=False)  # "straight_line" o "declining_balance"

    # Estado
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Multi-tenant: organization relationship
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="equipment")
    deleted_by = relationship("User", foreign_keys=[deleted_by_id])


# Índices adicionales para optimización
Index("ix_equipment_amortization_category", EquipmentAmortization.category)
# Note: organization_id, deleted_at, and is_active already have index=True in their Column definitions
