"""
Pydantic schemas for Annual Sales Projections
ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_serializer

from app.core.pydantic_config import DECIMAL_CONFIG


class AnnualSalesProjectionEntryCreate(BaseModel):
    """Schema for creating a projection entry"""

    service_id: int = Field(..., description="Service ID")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    quantity: int = Field(default=0, ge=0, description="Quantity of services to sell")
    hours_per_unit: float = Field(default=0.0, ge=0.0, description="Hours per unit of service")


class AnnualSalesProjectionCreate(BaseModel):
    """Schema for creating an annual sales projection"""

    year: int = Field(..., ge=2020, le=2100, description="Year of projection")
    notes: str | None = Field(None, description="Additional notes")
    entries: list[AnnualSalesProjectionEntryCreate] = Field(
        default_factory=list, description="List of projection entries"
    )


class AnnualSalesProjectionEntryUpdate(BaseModel):
    """Schema for updating a projection entry"""

    quantity: int | None = Field(None, ge=0)
    hours_per_unit: float | None = Field(None, ge=0.0)


class AnnualSalesProjectionEntryResponse(BaseModel):
    """Schema for projection entry response"""

    id: int
    service_id: int
    service_name: str = Field(..., description="Service name (joined from Service)")
    month: int
    quantity: int
    hours_per_unit: float

    class Config:
        from_attributes = True


class MonthlySummary(BaseModel):
    """Monthly summary calculated from projection"""

    month: int
    month_name: str  # "Enero", "Febrero", etc.
    total_revenue: Decimal = Field(..., description="Total revenue for the month")
    total_hours: float = Field(..., description="Total hours for the month")
    service_breakdown: list[dict[str, Any]] = Field(
        default_factory=list, description="Breakdown by service"
    )

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer("total_revenue")
    def serialize_total_revenue(self, value: Decimal) -> str:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class AnnualSalesProjectionResponse(BaseModel):
    """Schema for annual sales projection response"""

    id: int
    organization_id: int
    year: int
    is_active: bool
    notes: str | None
    entries: list[AnnualSalesProjectionEntryResponse] = Field(default_factory=list)
    summary: list[MonthlySummary] = Field(
        default_factory=list, description="Calculated monthly summary"
    )
    total_annual_revenue: Decimal = Field(..., description="Total annual revenue projected")
    total_annual_hours: float = Field(..., description="Total annual hours projected")
    break_even_monthly_cost: Decimal = Field(
        ..., description="Monthly break-even cost (Overhead + Payroll)"
    )
    created_at: datetime
    updated_at: datetime | None
    created_by_id: int

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer("total_annual_revenue", "break_even_monthly_cost")
    def serialize_decimal(self, value: Decimal) -> str:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class BulkUpdateEntriesRequest(BaseModel):
    """Schema for bulk updating projection entries"""

    entries: list[AnnualSalesProjectionEntryCreate] = Field(
        ..., description="List of entries to upsert", min_items=1
    )


class ReplicateMonthRequest(BaseModel):
    """Schema for replicating month values"""

    source_month: int = Field(..., ge=1, le=12, description="Source month to copy from")
    target_months: list[int] | None = Field(
        None, description="Target months to copy to (if None, copies to all months)"
    )
