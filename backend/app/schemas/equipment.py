"""
Schemas for equipment amortization endpoints.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer


class EquipmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str = Field(..., min_length=1, max_length=100)
    purchase_price: Decimal = Field(..., gt=0)
    purchase_date: date
    currency: str = Field(..., min_length=3, max_length=3)
    exchange_rate_at_purchase: Decimal | None = Field(None, gt=0)
    useful_life_months: int = Field(..., ge=1, le=600)
    salvage_value: Decimal = Field(default=Decimal("0"), ge=0)
    depreciation_method: str = Field(default="straight_line")
    is_active: bool = True


class EquipmentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(None, min_length=1, max_length=100)
    purchase_price: Decimal | None = Field(None, gt=0)
    purchase_date: date | None = None
    currency: str | None = Field(None, min_length=3, max_length=3)
    exchange_rate_at_purchase: Decimal | None = Field(None, gt=0)
    useful_life_months: int | None = Field(None, ge=1, le=600)
    salvage_value: Decimal | None = Field(None, ge=0)
    depreciation_method: str | None = None
    is_active: bool | None = None


class EquipmentResponse(BaseModel):
    id: int
    name: str
    description: str | None
    category: str
    purchase_price: Decimal
    purchase_date: date
    currency: str
    exchange_rate_at_purchase: Decimal | None
    useful_life_months: int
    salvage_value: Decimal
    depreciation_method: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

    @field_serializer("purchase_price", "exchange_rate_at_purchase", "salvage_value")
    def serialize_decimal_as_string(self, value: Decimal | None) -> str | None:
        return str(value) if value is not None else None


class EquipmentListResponse(BaseModel):
    items: list[EquipmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
