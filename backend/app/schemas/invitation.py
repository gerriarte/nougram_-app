"""
Pydantic schemas for Invitation management
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, validator


class InvitationBase(BaseModel):
    """Base schema for invitation"""

    email: EmailStr = Field(..., description="Email address to invite")
    role: str = Field(..., description="Role to assign when invitation is accepted")


class InvitationCreate(InvitationBase):
    """Schema for creating a new invitation"""

    pass


class InvitationResponse(BaseModel):
    """Schema for invitation response"""

    id: int
    organization_id: int
    email: str
    role: str
    token: str  # Only include token in specific contexts (e.g., when creating)
    expires_at: datetime
    accepted_at: datetime | None = None
    created_by_id: int
    created_at: datetime
    updated_at: datetime | None = None
    status: str  # pending, accepted, expired

    class Config:
        from_attributes = True


class InvitationListResponse(BaseModel):
    """Schema for list of invitations"""

    items: list[InvitationResponse]
    total: int


class InvitationAcceptRequest(BaseModel):
    """Schema for accepting an invitation"""

    token: str = Field(..., description="Invitation token")
    password: str | None = Field(None, description="Password for new user (if user doesn't exist)")
    full_name: str | None = Field(
        None, description="Full name for new user (if user doesn't exist)"
    )

    @validator("password")
    def validate_password(cls, v, values):
        """Validate password if provided"""
        if v is not None:
            if len(v) < 8:
                raise ValueError("Password must be at least 8 characters long")
        return v


class InvitationAcceptResponse(BaseModel):
    """Schema for invitation acceptance response"""

    success: bool
    message: str
    access_token: str | None = None  # JWT token for automatic login
    user_id: int | None = None
    organization_id: int | None = None
