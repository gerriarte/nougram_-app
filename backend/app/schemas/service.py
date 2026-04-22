"""
Pydantic schemas for Services
ESTÁNDAR NOUGRAM: Campos monetarios y porcentajes usan Decimal serializado como string
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer

from app.core.pydantic_config import DECIMAL_CONFIG


class ServiceBase(BaseModel):
    """Base schema for services (Sprint 14: supports multiple pricing types)
    ESTÁNDAR NOUGRAM: Campos monetarios y porcentajes usan Decimal para precisión
    """

    name: str = Field(..., description="Service name", min_length=1)
    description: str | None = Field(None, description="Service description")
    default_margin_target: Decimal = Field(
        Decimal("0.40"), description="Default profit margin target", ge=0, le=1
    )
    is_active: bool = Field(True, description="Whether the service is active")
    pricing_type: str | None = Field(
        "hourly", description="Pricing type: 'hourly', 'fixed', 'recurring', 'project_value'"
    )
    fixed_price: Decimal | None = Field(None, description="Fixed price (for fixed pricing)", ge=0)
    is_recurring: bool | None = Field(False, description="Whether service is recurring")
    billing_frequency: str | None = Field(
        None, description="Billing frequency: 'monthly', 'annual' (for recurring)"
    )
    recurring_price: Decimal | None = Field(
        None, description="Recurring price (for recurring pricing)", ge=0
    )

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer("default_margin_target", "fixed_price", "recurring_price")
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class ServiceCreate(ServiceBase):
    """Schema for creating a service"""

    pass


class ServiceUpdate(BaseModel):
    """Schema for updating a service (Sprint 14: supports multiple pricing types)
    ESTÁNDAR NOUGRAM: Campos monetarios y porcentajes usan Decimal para precisión
    """

    name: str | None = Field(None, min_length=1)
    description: str | None = None
    default_margin_target: Decimal | None = Field(None, ge=0, le=1)
    is_active: bool | None = None
    pricing_type: str | None = Field(
        None, description="Pricing type: 'hourly', 'fixed', 'recurring', 'project_value'"
    )
    fixed_price: Decimal | None = Field(None, ge=0)
    is_recurring: bool | None = None
    billing_frequency: str | None = None
    recurring_price: Decimal | None = Field(None, ge=0)

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer("default_margin_target", "fixed_price", "recurring_price")
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class ServiceResponse(ServiceBase):
    """Schema for service response"""

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    deleted_by_id: int | None = None
    deleted_by_name: str | None = None
    deleted_by_email: str | None = None

    class Config:
        from_attributes = True


class ServiceListResponse(BaseModel):
    """Schema for list of services"""

    items: list[ServiceResponse]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1
