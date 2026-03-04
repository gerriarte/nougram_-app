"""
Schemas for proposal documents.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProposalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    body_json: Dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="draft")


class ProposalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    body_json: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    is_locked: Optional[bool] = None


class ProposalGenerateAIRequest(BaseModel):
    title: Optional[str] = None
    language: str = Field(default="es", pattern="^(es|en)$")
    extra_instructions: Optional[str] = None


class ProposalResponse(BaseModel):
    id: int
    project_id: int
    organization_id: int
    version: int
    title: str
    body_json: Dict[str, Any]
    status: str
    is_locked: bool
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProposalListResponse(BaseModel):
    items: List[ProposalResponse]
    total: int
