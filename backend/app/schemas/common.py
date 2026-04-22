"""
Common Pydantic schemas
"""

from datetime import datetime

from pydantic import BaseModel, Field


class TimestampMixin(BaseModel):
    """Common timestamp fields"""

    created_at: datetime | None = None
    updated_at: datetime | None = None


class ResponseBase(BaseModel):
    """Base response model"""

    success: bool = True
    message: str | None = None


class ErrorResponse(ResponseBase):
    """Error response model"""

    success: bool = False
    error: str
    detail: str | None = None


class PaginationParams(BaseModel):
    """Pagination parameters"""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")

    @property
    def offset(self) -> int:
        """Calculate offset from page and page_size"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit (same as page_size)"""
        return self.page_size
