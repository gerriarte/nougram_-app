"""
Schemas for equipment amortization endpoints.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field, field_serializer


class EquipmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: str = Field(..., min_length=1, max_length=100)
    purchase_price: Decimal = Field(..., gt=0)
    purchase_date: date
    currency: str = Field(..., min_length=3, max_length=3)
    exchange_rate_at_purchase: Optional[Decimal] = Field(None, gt=0)
    useful_life_months: int = Field(..., ge=1, le=600)
    salvage_value: Decimal = Field(default=Decimal("0"), ge=0)
    depreciation_method: str = Field(default="straight_line")
    is_active: bool = True


class EquipmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    purchase_price: Optional[Decimal] = Field(None, gt=0)
    purchase_date: Optional[date] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    exchange_rate_at_purchase: Optional[Decimal] = Field(None, gt=0)
    useful_life_months: Optional[int] = Field(None, ge=1, le=600)
    salvage_value: Optional[Decimal] = Field(None, ge=0)
    depreciation_method: Optional[str] = None
    is_active: Optional[bool] = None


class EquipmentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: str
    purchase_price: Decimal
    purchase_date: date
    currency: str
    exchange_rate_at_purchase: Optional[Decimal]
    useful_life_months: int
    salvage_value: Decimal
    depreciation_method: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @field_serializer("purchase_price", "exchange_rate_at_purchase", "salvage_value")
    def serialize_decimal_as_string(self, value: Optional[Decimal]) -> Optional[str]:
        return str(value) if value is not None else None


class EquipmentListResponse(BaseModel):
    items: List[EquipmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
