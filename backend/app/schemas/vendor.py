"""
Pydantic schemas for the Vendor catalog.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer


class VendorBase(BaseModel):
    name: str = Field(..., min_length=1, description="Vendor name")
    description: str | None = None
    category: str | None = None
    default_cost: Decimal | None = Field(None, ge=0)
    default_markup_percentage: Decimal | None = Field(None, ge=0)
    is_active: bool = True

    @field_serializer("default_cost", "default_markup_percentage", when_used="json")
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        return str(value) if value is not None else None


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: str | None = Field(None, min_length=1)
    description: str | None = None
    category: str | None = None
    default_cost: Decimal | None = Field(None, ge=0)
    default_markup_percentage: Decimal | None = Field(None, ge=0)
    is_active: bool | None = None

    @field_serializer("default_cost", "default_markup_percentage", when_used="json")
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        return str(value) if value is not None else None


class VendorResponse(VendorBase):
    id: int
    organization_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    class Config:
        from_attributes = True


class VendorListResponse(BaseModel):
    items: list[VendorResponse]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1
