"""
Pydantic schemas for Industry Templates
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SuggestedRole(BaseModel):
    """Schema for suggested role in template"""

    name: str
    monthly_cost: float = Field(..., description="Monthly cost in USD")
    weekly_hours: int = Field(default=40, ge=1, le=168)
    seniority: str | None = Field(None, description="junior, middle, senior")


class SuggestedService(BaseModel):
    """Schema for suggested service in template"""

    name: str
    default_hourly_rate: float | None = Field(None, description="Default hourly rate in USD")
    category: str
    description: str | None = None


class SuggestedCost(BaseModel):
    """Schema for suggested fixed cost in template"""

    name: str
    amount: float = Field(..., description="Monthly amount in USD")
    category: str
    description: str | None = None
    adjust_by_region: bool = Field(
        default=False, description="Whether to adjust by region multiplier"
    )


class IndustryTemplateResponse(BaseModel):
    """Schema for industry template response"""

    id: int
    industry_type: str
    name: str
    description: str | None
    suggested_roles: list[dict[str, Any]] | None
    suggested_services: list[dict[str, Any]] | None
    suggested_fixed_costs: list[dict[str, Any]] | None
    is_active: bool
    icon: str | None
    color: str | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class IndustryTemplateListResponse(BaseModel):
    """Schema for list of templates"""

    items: list[IndustryTemplateResponse]
    total: int


class ApplyTemplateRequest(BaseModel):
    """Schema for applying a template to an organization"""

    industry_type: str = Field(..., description="Type of industry template to apply")
    region: str = Field(default="US", description="Region code for salary adjustment")
    currency: str = Field(default="USD", description="Currency code")
    customize: dict[str, Any] | None = Field(
        None, description="Optional customization data to override template defaults"
    )


class ApplyTemplateResponse(BaseModel):
    """Schema for template application response"""

    success: bool
    message: str
    template_applied: str
    region: str
    multiplier: float
    currency: str
    team_members_created: int
    services_created: int
    costs_created: int
    created_items: list[dict[str, Any]]
