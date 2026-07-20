"""
Pydantic schemas for the Quote Agent (chat) module.

The estimate breakdown mirrors the shape produced by
``calculate_quote_totals_enhanced`` so the frontend renders the same numbers the
deterministic engine computes — the LLM never emits amounts.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ConversationCreateResponse(BaseModel):
    id: int
    status: str


class ConversationSummary(BaseModel):
    id: int
    status: str
    project_id: int | None = None
    quote_id: int | None = None
    created_at: datetime | None = None


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str | None = None
    meta: dict | None = None
    created_at: datetime | None = None


class ConversationDetail(BaseModel):
    id: int
    status: str
    project_id: int | None = None
    quote_id: int | None = None
    created_at: datetime | None = None
    messages: list[MessageResponse] = Field(default_factory=list)


class EstimateItem(BaseModel):
    service_id: int
    service_name: str | None = None
    pricing_type: str | None = None
    estimated_hours: float | None = None
    quantity: float | None = None
    internal_cost: float = 0.0
    client_price: float = 0.0
    margin_percentage: float = 0.0


class EstimateBreakdown(BaseModel):
    """Deterministic engine output for the current proposal (no persistence)."""

    items: list[EstimateItem] = Field(default_factory=list)
    total_internal_cost: float = 0.0
    total_client_price: float = 0.0
    margin_percentage: float = 0.0
    target_margin_percentage: float | None = None
    minimum_margin_threshold: float | None = None
    below_minimum_margin: bool = False


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, description="User message in natural language")


class SendMessageResponse(BaseModel):
    assistant_message: MessageResponse
    estimate: EstimateBreakdown | None = None


class ConfirmRequest(BaseModel):
    client_name: str = Field(..., min_length=1)
    client_email: str | None = None
    project_name: str | None = Field(
        None, description="Defaults to a name derived from the client if omitted"
    )
    tax_ids: list[int] | None = Field(default_factory=list)
    target_margin_percentage: float | None = Field(None, ge=0, le=1)
    allow_low_margin: bool = False


class ConfirmResponse(BaseModel):
    project_id: int
    quote_id: int


class FeedbackItem(BaseModel):
    """A single agent-originated deal: what was proposed vs the final outcome."""

    conversation_id: int
    project_id: int | None = None
    quote_id: int | None = None
    status: str
    project_status: str | None = None
    outcome: str | None = None  # won | lost | accepted | rejected | pending
    decision_comment: str | None = None
    proposed_snapshot: dict | None = None
    final_total_client_price: float | None = None
    final_margin_percentage: float | None = None


class FeedbackDatasetResponse(BaseModel):
    items: list[FeedbackItem] = Field(default_factory=list)
