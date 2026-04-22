"""
Pydantic schemas for Fixed Costs
ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_serializer

from app.core.pydantic_config import DECIMAL_CONFIG

CurrencyCode = Literal["USD", "COP", "ARS", "EUR", "PEN", "MXN"]


class CostFixedBase(BaseModel):
    """Base schema for fixed costs
    ESTÁNDAR NOUGRAM: amount_monthly usa Decimal para precisión
    """

    name: str = Field(..., description="Cost name", min_length=1)
    amount_monthly: Decimal = Field(..., description="Monthly amount", gt=0)
    currency: CurrencyCode = Field(
        "USD", description="Currency code (USD, COP, ARS, EUR, PEN, MXN)"
    )
    category: str = Field(..., description="Cost category (e.g., 'Overhead', 'Software')")
    description: str | None = Field(None, description="Cost description")

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer("amount_monthly")
    def serialize_amount_monthly(self, value: Decimal) -> str:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class CostFixedCreate(CostFixedBase):
    """Schema for creating a fixed cost"""

    pass


class CostFixedUpdate(BaseModel):
    """Schema for updating a fixed cost
    ESTÁNDAR NOUGRAM: amount_monthly usa Decimal para precisión
    """

    name: str | None = Field(None, min_length=1)
    amount_monthly: Decimal | None = Field(None, gt=0)
    currency: CurrencyCode | None = None
    category: str | None = None
    description: str | None = None

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer("amount_monthly")
    def serialize_amount_monthly(self, value: Decimal | None) -> str | None:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class CostFixedResponse(CostFixedBase):
    """Schema for fixed cost response"""

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    deleted_by_id: int | None = None
    deleted_by_name: str | None = None
    deleted_by_email: str | None = None

    class Config:
        from_attributes = True


class CostFixedListResponse(BaseModel):
    """Schema for list of fixed costs"""

    items: list[CostFixedResponse]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1
