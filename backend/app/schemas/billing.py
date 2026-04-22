"""
Billing and subscription schemas
ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_serializer

from app.core.pydantic_config import DECIMAL_CONFIG


class CheckoutSessionCreate(BaseModel):
    """Request to create a checkout session"""

    plan: str = Field(..., description="Plan name (free, starter, professional, enterprise)")
    interval: str = Field("month", description="Billing interval (month or year)")
    success_url: str = Field(..., description="URL to redirect after successful payment")
    cancel_url: str = Field(..., description="URL to redirect after cancelled payment")


class CheckoutSessionResponse(BaseModel):
    """Response with checkout session URL"""

    session_id: str
    url: str

    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    """Subscription details response"""

    id: int
    organization_id: int
    stripe_subscription_id: str | None = None
    stripe_customer_id: str | None = None
    stripe_price_id: str | None = None
    plan: str
    status: str
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False
    canceled_at: datetime | None = None
    trial_start: datetime | None = None
    trial_end: datetime | None = None
    latest_invoice_id: str | None = None
    default_payment_method: str | None = None
    billing_provider: str | None = None
    manual_mode: bool = False
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class SubscriptionUpdate(BaseModel):
    """Request to update subscription"""

    plan: str | None = Field(None, description="New plan name")
    interval: str | None = Field(None, description="Billing interval (month or year)")
    cancel_at_period_end: bool | None = Field(None, description="Cancel at end of period")


class SubscriptionCancel(BaseModel):
    """Request to cancel subscription"""

    cancel_immediately: bool = Field(
        False, description="Cancel immediately instead of at period end"
    )


class ManualBillingRequestCreate(BaseModel):
    """Request payload for manual billing/account action."""

    request_type: str = Field(
        ...,
        description="Action type: change_plan, cancel_subscription, update_payment_method, account_action",
    )
    target_plan: str | None = Field(
        None, description="Target plan when request_type is change_plan"
    )
    target_interval: str | None = Field(None, description="Target interval (month/year)")
    notes: str | None = Field(None, description="Additional details for support/super admin")


class ManualBillingRequestResponse(BaseModel):
    """Created manual billing request."""

    id: int
    organization_id: int
    requested_by_user_id: int
    request_type: str
    target_plan: str | None = None
    target_interval: str | None = None
    notes: str | None = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PlanInfo(BaseModel):
    """Plan information
    ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal para precisión
    """

    name: str
    display_name: str
    description: str
    monthly_price: Decimal | None = None
    yearly_price: Decimal | None = None
    features: list[str] = []
    limits: dict[str, Any] = {}

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer("monthly_price", "yearly_price")
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class PlansListResponse(BaseModel):
    """List of available plans"""

    plans: list[PlanInfo]


class BillingPortalResponse(BaseModel):
    """Response with billing portal URL"""

    url: str
