"""
Billing and subscription schemas
ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal serializado como string
"""
from pydantic import BaseModel, Field, field_serializer
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
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
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    stripe_price_id: Optional[str] = None
    plan: str
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    latest_invoice_id: Optional[str] = None
    default_payment_method: Optional[str] = None
    billing_provider: Optional[str] = None
    manual_mode: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SubscriptionUpdate(BaseModel):
    """Request to update subscription"""
    plan: Optional[str] = Field(None, description="New plan name")
    interval: Optional[str] = Field(None, description="Billing interval (month or year)")
    cancel_at_period_end: Optional[bool] = Field(None, description="Cancel at end of period")


class SubscriptionCancel(BaseModel):
    """Request to cancel subscription"""
    cancel_immediately: bool = Field(False, description="Cancel immediately instead of at period end")


class PlanInfo(BaseModel):
    """Plan information
    ESTÁNDAR NOUGRAM: Campos monetarios usan Decimal para precisión
    """
    name: str
    display_name: str
    description: str
    monthly_price: Optional[Decimal] = None
    yearly_price: Optional[Decimal] = None
    features: list[str] = []
    limits: Dict[str, Any] = {}
    
    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer('monthly_price', 'yearly_price')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[str]:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None
    
    model_config = DECIMAL_CONFIG


class PlansListResponse(BaseModel):
    """List of available plans"""
    plans: list[PlanInfo]


class BillingPortalResponse(BaseModel):
    """Response with billing portal URL"""
    url: str










