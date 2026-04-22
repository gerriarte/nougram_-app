"""
Pydantic schemas for Team Members
ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_serializer

from app.core.pydantic_config import DECIMAL_CONFIG

CurrencyCode = Literal["USD", "COP", "ARS", "EUR", "PEN", "MXN"]


class TeamMemberBase(BaseModel):
    """Base schema for team members
    ESTÁNDAR NOUGRAM: salary_monthly_brute usa Decimal para precisión
    """

    name: str = Field(..., description="Team member name", min_length=1)
    role: str = Field(..., description="Team member role", min_length=1)
    salary_monthly_brute: Decimal = Field(..., description="Monthly gross salary", gt=0)
    currency: CurrencyCode = Field(
        "USD", description="Currency code (USD, COP, ARS, EUR, PEN, MXN)"
    )
    billable_hours_per_week: int = Field(32, description="Billable hours per week", ge=0, le=80)
    non_billable_hours_percentage: Decimal = Field(
        0, description="Non-billable hours percentage (0-1)", ge=0, le=1
    )
    apply_social_charges: bool = Field(
        True,
        description="Apply organization social charges multiplier to this member's salary in cost calculations",
    )
    is_active: bool | None = Field(True, description="Whether the team member is active")
    user_id: int | None = Field(None, description="Associated user ID")

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer("salary_monthly_brute", when_used="json")
    def serialize_salary(self, value: Decimal) -> str:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    @field_serializer("non_billable_hours_percentage", when_used="json")
    def serialize_non_billable(self, value: Decimal) -> str:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else "0"

    model_config = DECIMAL_CONFIG


class TeamMemberCreate(TeamMemberBase):
    """Schema for creating a team member"""

    pass


class TeamMemberUpdate(BaseModel):
    """Schema for updating a team member
    ESTÁNDAR NOUGRAM: salary_monthly_brute usa Decimal para precisión
    """

    name: str | None = Field(None, min_length=1)
    role: str | None = Field(None, min_length=1)
    salary_monthly_brute: Decimal | None = Field(None, gt=0)
    currency: CurrencyCode | None = None
    billable_hours_per_week: int | None = Field(None, ge=0, le=80)
    non_billable_hours_percentage: Decimal | None = Field(None, ge=0, le=1)
    apply_social_charges: bool | None = None
    is_active: bool | None = None
    user_id: int | None = None

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer("salary_monthly_brute", when_used="json")
    def serialize_salary(self, value: Decimal | None) -> str | None:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    @field_serializer("non_billable_hours_percentage", when_used="json")
    def serialize_non_billable(self, value: Decimal | None) -> str | None:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class TeamMemberResponse(TeamMemberBase):
    """Schema for team member response"""

    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class TeamMemberListResponse(BaseModel):
    """Schema for list of team members"""

    items: list[TeamMemberResponse]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1


class TeamMemberAllocationResponse(BaseModel):
    """Schema for resource allocation context (non-sensitive fields only)"""

    id: int
    name: str
    role: str
    billable_hours_per_week: int
    non_billable_hours_percentage: Decimal | None = None
    is_active: bool | None = True

    @field_serializer("non_billable_hours_percentage", when_used="json")
    def serialize_non_billable(self, value: Decimal | None) -> str | None:
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class TeamMemberAllocationListResponse(BaseModel):
    """Schema for list of allocation members"""

    items: list[TeamMemberAllocationResponse]
    total: int
