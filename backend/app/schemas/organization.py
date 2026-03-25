"""
Pydantic schemas for Organization management
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
import re


class OrganizationBase(BaseModel):
    """Base schema for organization"""
    name: str = Field(..., description="Organization name", min_length=1, max_length=255)
    slug: Optional[str] = Field(None, description="URL-friendly organization identifier")
    subscription_plan: str = Field(
        default="free",
        description="Subscription plan: free, starter, professional, enterprise"
    )
    subscription_status: str = Field(
        default="active",
        description="Subscription status: active, cancelled, past_due, trialing"
    )
    settings: Optional[Dict[str, Any]] = Field(None, description="Organization settings (JSON)")

    @validator('slug', pre=True, always=True)
    def generate_slug(cls, v, values):
        """Generate slug from name if not provided"""
        if v is None and 'name' in values:
            # Convert name to slug: lowercase, replace spaces with hyphens, remove special chars
            slug = re.sub(r'[^\w\s-]', '', values['name'].lower())
            slug = re.sub(r'[-\s]+', '-', slug)
            return slug[:50]  # Limit length
        return v

    @validator('slug')
    def validate_slug(cls, v):
        """Validate slug format"""
        if v:
            if not re.match(r'^[a-z0-9-]+$', v):
                raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
            if len(v) < 3:
                raise ValueError('Slug must be at least 3 characters long')
            if len(v) > 50:
                raise ValueError('Slug must be at most 50 characters long')
        return v


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization"""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization"""
    name: Optional[str] = Field(None, description="Organization name", min_length=1, max_length=255)
    slug: Optional[str] = Field(None, description="URL-friendly organization identifier")
    subscription_plan: Optional[str] = Field(
        None,
        description="Subscription plan: free, starter, professional, enterprise"
    )
    subscription_status: Optional[str] = Field(
        None,
        description="Subscription status: active, cancelled, past_due, trialing"
    )
    settings: Optional[Dict[str, Any]] = Field(None, description="Organization settings (JSON)")

    @validator('slug')
    def validate_slug(cls, v):
        """Validate slug format"""
        if v:
            if not re.match(r'^[a-z0-9-]+$', v):
                raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
            if len(v) < 3:
                raise ValueError('Slug must be at least 3 characters long')
            if len(v) > 50:
                raise ValueError('Slug must be at most 50 characters long')
        return v


class OrganizationResponse(BaseModel):
    """Schema for organization response"""
    id: int
    name: str
    slug: str
    subscription_plan: str
    subscription_status: str
    settings: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_count: Optional[int] = Field(None, description="Number of users in the organization")

    class Config:
        from_attributes = True


class OrganizationListResponse(BaseModel):
    """Schema for organization list response"""
    items: List[OrganizationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class OrganizationRegisterRequest(BaseModel):
    """Schema for public organization registration"""
    organization_name: str = Field(..., description="Organization name", min_length=1, max_length=255)
    organization_slug: Optional[str] = Field(None, description="URL-friendly organization identifier")
    admin_email: str = Field(..., description="Admin user email")
    admin_full_name: str = Field(..., description="Admin user full name", min_length=1)
    admin_password: str = Field(..., description="Admin user password", min_length=8)
    subscription_plan: str = Field(default="free", description="Initial subscription plan")


class OrganizationInviteRequest(BaseModel):
    """Schema for inviting a user to an organization"""
    email: str = Field(..., description="Email address of the user to invite")
    role: str = Field(default="org_member", description="Role to assign: org_admin, org_member")
    message: Optional[str] = Field(None, description="Optional invitation message")


class OrganizationInviteResponse(BaseModel):
    """Schema for invitation response"""
    success: bool
    message: str
    invitation_token: Optional[str] = Field(None, description="Invitation token (for email links)")


class OrganizationUserResponse(BaseModel):
    """Schema for organization user response"""
    id: int
    email: str
    full_name: str
    role: str
    organization_id: int
    created_at: Optional[datetime] = None  # Optional since User model doesn't have created_at yet
    email_verified: Optional[bool] = None
    email_verified_at: Optional[datetime] = None
    job_title: Optional[str] = None
    specialty: Optional[str] = None

    class Config:
        from_attributes = True


class OrganizationUsersListResponse(BaseModel):
    """Schema for organization users list"""
    items: List[OrganizationUserResponse]
    total: int


class SocialChargesConfig(BaseModel):
    """Schema for social charges configuration (Ley 100 - Colombia)"""
    enable_social_charges: bool = Field(default=False, description="Enable social charges calculation")
    health_percentage: Optional[float] = Field(8.5, ge=0, le=100, description="Health percentage (Employer share)")
    pension_percentage: Optional[float] = Field(12.0, ge=0, le=100, description="Pension percentage (Employer share)")
    arl_percentage: Optional[float] = Field(0.522, ge=0, le=100, description="ARL percentage")
    parafiscales_percentage: Optional[float] = Field(4.0, ge=0, le=100, description="Caja de Compensación / Parafiscales percentage")
    
    # New breakdown for Colombia (Sprint 18)
    prima_services_percentage: Optional[float] = Field(8.33, ge=0, le=100, description="Provision for Prima de servicios")
    cesantias_percentage: Optional[float] = Field(8.33, ge=0, le=100, description="Provision for Cesantías")
    int_cesantias_percentage: Optional[float] = Field(1.0, ge=0, le=100, description="Provision for Intereses de cesantías")
    vacations_percentage: Optional[float] = Field(4.17, ge=0, le=100, description="Provision for Vacaciones")
    
    total_percentage: Optional[float] = Field(None, ge=0, le=200, description="Total multiplier percentage (e.g. 51.0 for ~1.51)")
    country_code: Optional[str] = Field(
        None,
        min_length=2,
        max_length=3,
        description="Country code used to source the preset (e.g. CO, MX, US)"
    )
    preset_key: Optional[str] = Field(
        None,
        max_length=32,
        description="Preset identifier applied by UI (for auditability)"
    )
    country_source: Optional[str] = Field(
        None,
        max_length=16,
        description="Source of country selection: account or custom"
    )
    version: Optional[int] = Field(
        None,
        ge=1,
        description="Client-managed config version for future change tracking"
    )
    updated_at: Optional[str] = Field(
        None,
        description="ISO timestamp of latest config update (set by client)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "enable_social_charges": True,
                "health_percentage": 8.5,
                "pension_percentage": 12.0,
                "arl_percentage": 0.522,
                "parafiscales_percentage": 4.0,
                "prima_services_percentage": 8.33,
                "cesantias_percentage": 8.33,
                "int_cesantias_percentage": 1.0,
                "vacations_percentage": 4.17,
                "total_percentage": 52.852,
                "country_code": "CO",
                "preset_key": "CO",
                "country_source": "account",
                "version": 1,
                "updated_at": "2026-03-16T18:30:00.000Z"
            }
        }


class OnboardingConfigRequest(BaseModel):
    """Schema for onboarding configuration request"""
    social_charges_config: Optional[SocialChargesConfig] = Field(None, description="Social charges configuration")
    tax_structure: Optional[Dict[str, Any]] = Field(None, description="Tax structure (IVA, ICA, retentions, etc.)")
    country: Optional[str] = Field(None, description="Country code")
    currency: Optional[str] = Field(None, description="Currency code")
    profile_type: Optional[str] = Field(None, description="Profile type (freelance, professional, company)")

    class Config:
        json_schema_extra = {
            "example": {
                "social_charges_config": {
                    "enable_social_charges": True,
                    "health_percentage": 8.5,
                    "pension_percentage": 12.0,
                    "arl_percentage": 0.522,
                    "parafiscales_percentage": 8.0
                },
                "tax_structure": {
                    "iva": 19.0,
                    "ica": 0.966,
                    "retentions": 11.0
                },
                "country": "COL",
                "currency": "COP",
                "profile_type": "company"
            }
        }


class OnboardingConfigResponse(BaseModel):
    """Schema for onboarding configuration response"""
    success: bool
    message: str
    organization_id: int
    settings: Optional[Dict[str, Any]] = None


class OrganizationUsageStatsResponse(BaseModel):
    """Schema for organization usage statistics"""
    organization_id: int
    organization_name: str
    subscription_plan: str
    current_usage: Dict[str, int] = Field(..., description="Current usage counts")
    limits: Dict[str, int] = Field(..., description="Plan limits (-1 means unlimited)")
    usage_percentage: Dict[str, float] = Field(..., description="Usage percentage per resource")


class AddUserToOrganizationRequest(BaseModel):
    """Schema for adding a user to an organization"""
    user_id: Optional[int] = Field(None, description="Existing user ID to add")
    email: Optional[str] = Field(None, description="Email of user to add (creates new user)")
    full_name: Optional[str] = Field(None, description="Full name (required if creating new user)")
    role: str = Field(default="org_member", description="Role to assign: org_admin, org_member")
    password: Optional[str] = Field(None, description="Password (required if creating new user)", min_length=8)


class UpdateUserRoleRequest(BaseModel):
    """Schema for updating user role in organization"""
    role: str = Field(..., description="New role: org_admin, org_member")


class UpdateSubscriptionPlanRequest(BaseModel):
    """Schema for updating subscription plan"""
    plan: str = Field(..., description="New subscription plan: free, starter, professional, enterprise")
    status: Optional[str] = Field(None, description="Subscription status: active, cancelled, past_due, trialing")

