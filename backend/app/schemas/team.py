"""
Pydantic schemas for Team Members
ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
"""
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_serializer
from app.core.pydantic_config import DECIMAL_CONFIG

CurrencyCode = Literal["USD", "COP", "ARS", "EUR"]


class TeamMemberBase(BaseModel):
    """Base schema for team members
    ESTÁNDAR NOUGRAM: salary_monthly_brute usa Decimal para precisión
    """
    name: str = Field(..., description="Team member name", min_length=1)
    role: str = Field(..., description="Team member role", min_length=1)
    salary_monthly_brute: Decimal = Field(..., description="Monthly gross salary", gt=0)
    currency: CurrencyCode = Field("USD", description="Currency code (USD, COP, ARS, EUR)")
    billable_hours_per_week: int = Field(32, description="Billable hours per week", ge=0, le=80)
    non_billable_hours_percentage: Decimal = Field(0, description="Non-billable hours percentage (0-1)", ge=0, le=1)
    is_active: Optional[bool] = Field(True, description="Whether the team member is active")
    user_id: Optional[int] = Field(None, description="Associated user ID")
    
    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer('salary_monthly_brute')
    def serialize_salary(self, value: Decimal) -> str:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    @field_serializer('non_billable_hours_percentage')
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
    name: Optional[str] = Field(None, min_length=1)
    role: Optional[str] = Field(None, min_length=1)
    salary_monthly_brute: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[CurrencyCode] = None
    billable_hours_per_week: Optional[int] = Field(None, ge=0, le=80)
    non_billable_hours_percentage: Optional[Decimal] = Field(None, ge=0, le=1)
    is_active: Optional[bool] = None
    user_id: Optional[int] = None
    
    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer('salary_monthly_brute')
    def serialize_salary(self, value: Optional[Decimal]) -> Optional[str]:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    @field_serializer('non_billable_hours_percentage')
    def serialize_non_billable(self, value: Optional[Decimal]) -> Optional[str]:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None
    
    model_config = DECIMAL_CONFIG


class TeamMemberResponse(TeamMemberBase):
    """Schema for team member response"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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
    non_billable_hours_percentage: Optional[Decimal] = None
    is_active: Optional[bool] = True

    @field_serializer('non_billable_hours_percentage')
    def serialize_non_billable(self, value: Optional[Decimal]) -> Optional[str]:
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class TeamMemberAllocationListResponse(BaseModel):
    """Schema for list of allocation members"""
    items: list[TeamMemberAllocationResponse]
    total: int

