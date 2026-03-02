"""
Pydantic schemas for Onboarding
ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
"""
from typing import Optional, List, Dict, Any, Literal
from decimal import Decimal
from pydantic import BaseModel, Field, field_serializer

from app.core.pydantic_config import DECIMAL_CONFIG


# Benchmarks
class ProfileBenchmark(BaseModel):
    """Benchmark values for a business profile"""
    profile_type: Literal["freelance", "company", "agency"]
    avg_monthly_income: Optional[Decimal] = Field(None, description="Average monthly income")
    avg_margin: Optional[Decimal] = Field(None, description="Average margin percentage")
    avg_hours_per_month: Optional[Decimal] = Field(None, description="Average billable hours per month")
    avg_team_size: Optional[int] = Field(None, description="Average team size")
    avg_salary: Optional[Decimal] = Field(None, description="Average salary")
    avg_clients: Optional[int] = Field(None, description="Average number of clients")
    
    @field_serializer('avg_monthly_income', 'avg_margin', 'avg_hours_per_month', 'avg_salary')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[str]:
        """Serialize Decimal as string"""
        return str(value) if value is not None else None
    
    model_config = DECIMAL_CONFIG


class BenchmarksResponse(BaseModel):
    """Response with benchmarks for a profile type"""
    profile_type: Literal["freelance", "company", "agency"]
    country: str
    currency: str
    benchmarks: ProfileBenchmark
    source: str = Field("industry_standard", description="Source of benchmarks")


# Complete Onboarding
class OnboardingTeamMember(BaseModel):
    """Team member data for onboarding"""
    name: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    salary_monthly_brute: Decimal = Field(..., gt=0)
    currency: str = Field("USD")
    billable_hours_per_month: int = Field(40, ge=1, le=200)  # Monthly hours
    
    @field_serializer('salary_monthly_brute')
    def serialize_decimal(self, value: Decimal) -> str:
        return str(value)
    
    model_config = DECIMAL_CONFIG


class OnboardingExpense(BaseModel):
    """Operational expense for onboarding"""
    name: str = Field(..., min_length=1)
    category: Literal["rent", "software", "services"] = Field(...)
    amount_monthly: Decimal = Field(..., gt=0)
    currency: str = Field("USD")
    quantity: int = Field(1, ge=1, description="Quantity of equal items included in total amount")
    
    @field_serializer('amount_monthly')
    def serialize_decimal(self, value: Decimal) -> str:
        return str(value)
    
    model_config = DECIMAL_CONFIG


class CompleteOnboardingRequest(BaseModel):
    """Request to save complete onboarding configuration"""
    # Organization data
    organization_name: Optional[str] = Field(None, min_length=1)
    organization_description: Optional[str] = None
    country: str = Field(..., min_length=2, max_length=3)
    currency: str = Field(..., min_length=3, max_length=3)
    profile_type: Literal["freelance", "company", "agency"] = Field(...)
    
    # Team members (optional, can be empty for freelance)
    team_members: List[OnboardingTeamMember] = Field(default_factory=list)
    
    # Operational expenses
    expenses: List[OnboardingExpense] = Field(default_factory=list)

    # Inventory snapshot (includes amortizable assets and tools selected in onboarding)
    inventory_items: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    
    # Tax structure (optional)
    tax_structure: Optional[Dict[str, Any]] = None
    
    # Social charges config (optional, mainly for Colombia)
    social_charges_config: Optional[Dict[str, Any]] = None


class CompleteOnboardingResponse(BaseModel):
    """Response after completing onboarding"""
    success: bool
    message: str
    organization_id: int
    team_members_created: int
    expenses_created: int
    bcr_calculated: Optional[str] = Field(None, description="Calculated BCR after onboarding")
    organization: Dict[str, Any] = Field(..., description="Updated organization data")


# Temporary BCR Calculation
class TemporaryBCRRequest(BaseModel):
    """Request to calculate BCR with temporary onboarding data"""
    team_members: List[OnboardingTeamMember] = Field(..., min_items=1)
    expenses: List[OnboardingExpense] = Field(default_factory=list)
    inventory_items: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    social_charges_config: Optional[Dict[str, Any]] = None
    currency: str = Field("USD")


class TemporaryBCRResponse(BaseModel):
    """Response with temporary BCR calculation"""
    blended_cost_rate: str = Field(..., description="Calculated BCR (Decimal as string)")
    total_monthly_costs: str = Field(..., description="Total monthly costs")
    total_fixed_overhead: str = Field(..., description="Total fixed overhead")
    total_salaries: str = Field(..., description="Total salaries")
    total_monthly_hours: float = Field(..., description="Total billable hours per month")
    team_members_count: int = Field(..., description="Number of team members")
    currency: str = Field(..., description="Currency code")
    note: str = Field(
        "Values are calculated with temporary data and may differ after saving",
        description="Disclaimer about temporary calculation"
    )
