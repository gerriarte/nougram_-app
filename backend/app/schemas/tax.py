"""
Pydantic schemas for Taxes
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer


class TaxBase(BaseModel):
    """Base schema for taxes"""

    name: str = Field(..., description="Tax name (e.g., IVA, Transaction Cost)", min_length=1)
    code: str = Field(..., description="Tax code (e.g., IVA_CO, TX_AR)", min_length=1)
    percentage: Decimal = Field(
        ..., description="Tax percentage (e.g., 19.0 for 19%)", ge=0, le=100
    )
    country: str | None = Field(None, description="Country code (e.g., CO, AR, US)")
    description: str | None = Field(None, description="Tax description")
    is_active: bool = Field(True, description="Whether the tax is active")

    @field_serializer("percentage", when_used="json")
    def serialize_percentage(self, value: Decimal) -> str:
        """Serialize Decimal as string to preserve precision."""
        return str(value)


class TaxCreate(TaxBase):
    """Schema for creating a tax"""

    pass


class TaxUpdate(BaseModel):
    """Schema for updating a tax"""

    name: str | None = Field(None, min_length=1)
    code: str | None = Field(None, min_length=1)
    percentage: Decimal | None = Field(None, ge=0, le=100)
    country: str | None = None
    description: str | None = None
    is_active: bool | None = None

    @field_serializer("percentage", when_used="json")
    def serialize_percentage(self, value: Decimal | None) -> str | None:
        """Serialize Decimal as string to preserve precision."""
        return str(value) if value is not None else None


class TaxResponse(TaxBase):
    """Schema for tax response"""

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    deleted_by_id: int | None = None
    deleted_by_name: str | None = None
    deleted_by_email: str | None = None

    class Config:
        from_attributes = True


class TaxListResponse(BaseModel):
    """Schema for list of taxes"""

    items: list[TaxResponse]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1
