"""
Pydantic schemas for Fixed Costs
ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
"""
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_serializer
from app.core.pydantic_config import DECIMAL_CONFIG

CurrencyCode = Literal["USD", "COP", "ARS", "EUR", "PEN", "MXN"]


class CostFixedBase(BaseModel):
    """Base schema for fixed costs
    ESTÁNDAR NOUGRAM: amount_monthly usa Decimal para precisión
    """
    name: str = Field(..., description="Cost name", min_length=1)
    amount_monthly: Decimal = Field(..., description="Monthly amount", gt=0)
    currency: CurrencyCode = Field("USD", description="Currency code (USD, COP, ARS, EUR, PEN, MXN)")
    category: str = Field(..., description="Cost category (e.g., 'Overhead', 'Software')")
    description: Optional[str] = Field(None, description="Cost description")
    
    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer('amount_monthly')
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
    name: Optional[str] = Field(None, min_length=1)
    amount_monthly: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[CurrencyCode] = None
    category: Optional[str] = None
    description: Optional[str] = None
    
    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer('amount_monthly')
    def serialize_amount_monthly(self, value: Optional[Decimal]) -> Optional[str]:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None
    
    model_config = DECIMAL_CONFIG


class CostFixedResponse(CostFixedBase):
    """Schema for fixed cost response"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    deleted_by_id: Optional[int] = None
    deleted_by_name: Optional[str] = None
    deleted_by_email: Optional[str] = None

    class Config:
        from_attributes = True


class CostFixedListResponse(BaseModel):
    """Schema for list of fixed costs"""
    items: list[CostFixedResponse]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1

