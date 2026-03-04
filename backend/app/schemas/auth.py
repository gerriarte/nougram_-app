"""
Pydantic schemas for Authentication
"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class LoginRequest(BaseModel):
    """Schema for email/password login"""
    email: str = Field(..., description="User email address", min_length=1)
    password: str = Field(..., min_length=1, description="User password")


class UserUpdate(BaseModel):
    """Schema for updating current user profile"""
    full_name: str = Field(..., description="User full name", min_length=1)


class GoogleLoginRequest(BaseModel):
    """Schema for Google OAuth login request"""
    code: str = Field(..., description="OAuth authorization code from Google")


class GoogleConnectRequest(BaseModel):
    """Schema for Google Calendar connection request"""
    code: str = Field(..., description="OAuth authorization code from Google")


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: dict = Field(..., description="User information")


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    email: EmailStr
    full_name: str
    has_calendar_connected: bool = False
    role: str = Field(default="product_manager", description="User role")  # Always str, never enum
    organization_id: Optional[int] = Field(None, description="Organization ID for multi-tenant support")
    email_verified: bool = Field(default=True, description="Whether user email is verified")

    class Config:
        from_attributes = False  # Disable to avoid enum issues


class UserListResponse(BaseModel):
    """Schema for user list response"""
    items: list[UserResponse]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1


class UserRoleUpdate(BaseModel):
    """Schema for updating user role"""
    role: str = Field(..., description="New role for the user")


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., description="User full name", min_length=1)
    role: str = Field(default="product_manager", description="User role")
    password: str = Field(..., min_length=8, description="Initial password for the user")


class SwitchOrganizationRequest(BaseModel):
    """Schema for switching organization"""
    organization_id: int = Field(..., description="Organization ID to switch to", gt=0)


class ForgotPasswordRequest(BaseModel):
    """Request password reset email."""
    email: EmailStr = Field(..., description="User email address")


class ForgotPasswordResponse(BaseModel):
    """Generic response for forgot password requests."""
    message: str


class ResetPasswordRequest(BaseModel):
    """Reset password using a valid token."""
    token: str = Field(..., min_length=16, description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")


class ResetPasswordResponse(BaseModel):
    """Response after successful password reset."""
    message: str


class VerifyEmailRequest(BaseModel):
    """Request to verify user email using token."""
    token: str = Field(..., min_length=16, description="Email verification token")


class VerifyEmailResponse(BaseModel):
    """Response after successful email verification."""
    message: str