"""
Billing gateway abstraction to support multiple payment providers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class BillingGatewayError(Exception):
    """Base error for billing gateway operations."""


@dataclass
class CheckoutSessionResult:
    session_id: str
    url: str


@dataclass
class ExternalSubscriptionResult:
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    external_price_id: Optional[str] = None


class BillingGateway(ABC):
    """Common contract for external billing providers."""

    provider_name: str

    @property
    @abstractmethod
    def supports_checkout(self) -> bool:
        """Whether provider supports hosted checkout sessions."""

    @property
    @abstractmethod
    def supports_webhooks(self) -> bool:
        """Whether provider supports webhooks handled by this service."""

    @abstractmethod
    def get_price_id(self, plan: str, interval: str = "month") -> Optional[str]:
        """Map internal plan+interval to provider price id."""

    @abstractmethod
    def ensure_customer_id(
        self,
        existing_customer_id: Optional[str],
        email: str,
        organization_name: str,
        organization_id: int,
    ) -> Optional[str]:
        """Reuse or create external customer id."""

    @abstractmethod
    def create_checkout_session(
        self,
        customer_id: Optional[str],
        price_id: str,
        success_url: str,
        cancel_url: str,
        organization_id: int,
        plan: str,
        interval: str,
    ) -> CheckoutSessionResult:
        """Create external checkout session."""

    @abstractmethod
    def update_subscription(
        self,
        external_subscription_id: str,
        plan: Optional[str],
        interval: Optional[str],
        cancel_at_period_end: Optional[bool],
    ) -> ExternalSubscriptionResult:
        """Update external subscription."""

    @abstractmethod
    def cancel_subscription(
        self,
        external_subscription_id: str,
        cancel_immediately: bool,
    ) -> ExternalSubscriptionResult:
        """Cancel external subscription."""


class ManualBillingGateway(BillingGateway):
    """
    Local/manual provider: no external checkout/subscription API.
    This keeps the system provider-agnostic when no gateway is enabled yet.
    """

    provider_name = "manual"

    @property
    def supports_checkout(self) -> bool:
        return False

    @property
    def supports_webhooks(self) -> bool:
        return False

    def get_price_id(self, plan: str, interval: str = "month") -> Optional[str]:
        return None

    def ensure_customer_id(
        self,
        existing_customer_id: Optional[str],
        email: str,
        organization_name: str,
        organization_id: int,
    ) -> Optional[str]:
        return existing_customer_id

    def create_checkout_session(
        self,
        customer_id: Optional[str],
        price_id: str,
        success_url: str,
        cancel_url: str,
        organization_id: int,
        plan: str,
        interval: str,
    ) -> CheckoutSessionResult:
        raise BillingGatewayError(
            "Checkout is not available for manual billing provider."
        )

    def update_subscription(
        self,
        external_subscription_id: str,
        plan: Optional[str],
        interval: Optional[str],
        cancel_at_period_end: Optional[bool],
    ) -> ExternalSubscriptionResult:
        raise BillingGatewayError(
            "External subscription updates are not available for manual provider."
        )

    def cancel_subscription(
        self,
        external_subscription_id: str,
        cancel_immediately: bool,
    ) -> ExternalSubscriptionResult:
        raise BillingGatewayError(
            "External subscription cancel is not available for manual provider."
        )


class StripeBillingGateway(BillingGateway):
    """Adapter that implements BillingGateway using Stripe service."""

    provider_name = "stripe"

    def __init__(self) -> None:
        from app.core.stripe_service import stripe_service

        self._stripe = stripe_service

    @property
    def supports_checkout(self) -> bool:
        return True

    @property
    def supports_webhooks(self) -> bool:
        return True

    def get_price_id(self, plan: str, interval: str = "month") -> Optional[str]:
        return self._stripe.get_price_id(plan, interval)

    def ensure_customer_id(
        self,
        existing_customer_id: Optional[str],
        email: str,
        organization_name: str,
        organization_id: int,
    ) -> Optional[str]:
        if existing_customer_id:
            return existing_customer_id
        customer = self._stripe.create_customer(
            email=email,
            name=organization_name,
            organization_id=organization_id,
        )
        return customer.id

    def create_checkout_session(
        self,
        customer_id: Optional[str],
        price_id: str,
        success_url: str,
        cancel_url: str,
        organization_id: int,
        plan: str,
        interval: str,
    ) -> CheckoutSessionResult:
        session = self._stripe.create_checkout_session(
            customer_id=customer_id,
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url,
            organization_id=organization_id,
            mode="subscription",
            metadata={"plan": plan, "interval": interval},
        )
        return CheckoutSessionResult(session_id=session.id, url=session.url)

    def update_subscription(
        self,
        external_subscription_id: str,
        plan: Optional[str],
        interval: Optional[str],
        cancel_at_period_end: Optional[bool],
    ) -> ExternalSubscriptionResult:
        price_id = None
        if plan:
            price_id = self.get_price_id(plan, interval or "month")
            if not price_id:
                raise BillingGatewayError(
                    f"Price ID not configured for plan {plan} with interval {interval or 'month'}"
                )

        updated = self._stripe.update_subscription(
            subscription_id=external_subscription_id,
            price_id=price_id,
            cancel_at_period_end=cancel_at_period_end,
        )

        return ExternalSubscriptionResult(
            status=updated.status,
            current_period_start=datetime.fromtimestamp(
                updated.current_period_start, tz=timezone.utc
            )
            if getattr(updated, "current_period_start", None)
            else None,
            current_period_end=datetime.fromtimestamp(
                updated.current_period_end, tz=timezone.utc
            )
            if getattr(updated, "current_period_end", None)
            else None,
            cancel_at_period_end=bool(updated.cancel_at_period_end),
            external_price_id=price_id,
        )

    def cancel_subscription(
        self,
        external_subscription_id: str,
        cancel_immediately: bool,
    ) -> ExternalSubscriptionResult:
        updated = self._stripe.cancel_subscription(
            subscription_id=external_subscription_id,
            cancel_at_period_end=not cancel_immediately,
        )
        status = "cancelled" if cancel_immediately else getattr(updated, "status", "active")
        return ExternalSubscriptionResult(
            status=status,
            cancel_at_period_end=not cancel_immediately,
        )


def get_billing_gateway() -> BillingGateway:
    """
    Build gateway instance based on configured provider.
    Supported: stripe, manual.
    """
    provider = (settings.PAYMENT_GATEWAY_PROVIDER or "manual").strip().lower()
    if provider == "stripe":
        return StripeBillingGateway()
    if provider == "manual":
        return ManualBillingGateway()

    logger.warning(
        f"Unknown PAYMENT_GATEWAY_PROVIDER '{provider}'. Falling back to manual provider."
    )
    return ManualBillingGateway()
