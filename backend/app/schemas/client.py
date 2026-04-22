"""
Pydantic schemas for Client (master catalog).
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ClientBase(BaseModel):
    """Base schema for clients."""

    display_name: str = Field(..., min_length=1, description="Company / display name")
    requester_name: str | None = Field(None, description="Contact person name")
    email: str | None = Field(None, description="Contact email")
    status: str = Field("active", description="active | inactive")
    notes: str | None = None


class ClientCreate(ClientBase):
    """Schema for creating a client."""

    pass


class ClientUpdate(BaseModel):
    """Schema for updating a client."""

    display_name: str | None = Field(None, min_length=1)
    requester_name: str | None = None
    email: str | None = None
    status: str | None = None
    notes: str | None = None


class ClientResponse(ClientBase):
    """Schema for client response."""

    id: int
    organization_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ClientSearchItem(BaseModel):
    """Item for autocomplete/search (GET /clients/search)."""

    id: int
    display_name: str
    requester_name: str | None = None
    email: str | None = None

    class Config:
        from_attributes = True


class ClientSearchResponse(BaseModel):
    """Response for GET /clients/search."""

    items: list[ClientSearchItem]
    total: int


class ClientListResponse(BaseModel):
    """Paginated list of clients."""

    items: list[ClientResponse]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1
