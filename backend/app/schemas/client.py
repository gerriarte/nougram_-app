"""
Pydantic schemas for Client (master catalog).
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ClientBase(BaseModel):
    """Base schema for clients."""
    display_name: str = Field(..., min_length=1, description="Company / display name")
    requester_name: Optional[str] = Field(None, description="Contact person name")
    email: Optional[str] = Field(None, description="Contact email")
    status: str = Field("active", description="active | inactive")
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    """Schema for creating a client."""
    pass


class ClientUpdate(BaseModel):
    """Schema for updating a client."""
    display_name: Optional[str] = Field(None, min_length=1)
    requester_name: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ClientResponse(ClientBase):
    """Schema for client response."""
    id: int
    organization_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ClientSearchItem(BaseModel):
    """Item for autocomplete/search (GET /clients/search)."""
    id: int
    display_name: str
    requester_name: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True


class ClientSearchResponse(BaseModel):
    """Response for GET /clients/search."""
    items: List[ClientSearchItem]
    total: int


class ClientListResponse(BaseModel):
    """Paginated list of clients."""
    items: List[ClientResponse]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1
