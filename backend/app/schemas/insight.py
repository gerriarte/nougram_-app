"""
Pydantic schemas for Insights and AI
"""

from typing import Literal

from pydantic import BaseModel, Field


class AIAdvisorRequest(BaseModel):
    """Schema for AI advisor request"""

    question: str = Field(..., description="Question to ask the AI advisor")
    ai_provider: str = Field(default="openai", description="AI provider: 'openai' or 'gemini'")


class AIAdvisorResponse(BaseModel):
    """Schema for AI advisor response"""

    success: bool = Field(..., description="Whether the query was successful")
    answer: str = Field(..., description="AI advisor response")
    provider: str | None = Field(None, description="AI provider used")


class DashboardKpiMeta(BaseModel):
    """Metadata for unified dashboard KPI response."""

    range_mode: Literal["relative", "custom"] = Field(
        ..., description="How the date window was built"
    )
    timezone: str = Field(..., description="IANA timezone used for range boundaries")
    applied_start: str = Field(..., description="Inclusive range start (ISO 8601, UTC)")
    applied_end: str = Field(..., description="Inclusive range end (ISO 8601, UTC)")
    months_back: int | None = Field(None, description="Only when range_mode=relative")
    custom_start_date: str | None = Field(
        None, description="Only when range_mode=custom (YYYY-MM-DD local)"
    )
    custom_end_date: str | None = Field(
        None, description="Only when range_mode=custom (YYYY-MM-DD local)"
    )
    latest_quote_only: bool = Field(
        True, description="Metrics use latest quote version per project"
    )
    exclude_draft: bool = Field(True, description="Projects in Draft are excluded")
    date_field: str = Field("quote.updated_at", description="Temporal filter field")


class DashboardKpiNumbers(BaseModel):
    """Unified KPI block (latest non-draft quote per project, date on quote.updated_at)."""

    totalCotizadoConImpuestos: float = Field(..., description="Sum of total with taxes")
    costoTotalOperacional: float = Field(..., description="Sum of total_internal_cost")
    margenNetoTotal: float = Field(..., description="Sum of (total with taxes - internal cost)")
    numeroPropuestasRealizadas: int = Field(
        ..., description="Projects counted (latest quote in window)"
    )
    numeroPropuestasGanadas: int = Field(..., description="Subset with project status Won")


class DashboardKpiSummaryResponse(BaseModel):
    """GET /insights/dashboard/kpi-summary contract."""

    meta: DashboardKpiMeta
    kpis: DashboardKpiNumbers
    currency: str = Field(..., description="Organization primary currency for display")
