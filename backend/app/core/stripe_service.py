"""
Stripe service for managing subscriptions and payments
"""

from typing import Any

import stripe

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Initialize Stripe (only if key is provided)
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY
else:
    logger.warning("STRIPE_SECRET_KEY not set. Stripe functionality will be limited.")


class StripeService:
    """Service for interacting with Stripe API"""

    @staticmethod
    def get_price_id(plan: str, interval: str = "month") -> str | None:
        """Get Stripe price ID for a plan and interval"""
        price_ids = settings.stripe_price_ids_dict
        plan_key = f"{plan}_{interval}"
        return price_ids.get(plan_key)

    @staticmethod
    def create_customer(
        email: str,
        name: str | None = None,
        organization_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:  # stripe.Customer
        """
        Create a customer in Stripe

        Args:
            email: Customer email
            name: Customer name (optional)
            organization_id: Organization ID for metadata
            metadata: Additional metadata

        Returns:
            Stripe Customer object
        """
        customer_data = {"email": email, "metadata": metadata or {}}

        if name:
            customer_data["name"] = name

        if organization_id:
            customer_data["metadata"]["organization_id"] = str(organization_id)

        try:
            customer = stripe.Customer.create(**customer_data)
            logger.info(f"Created Stripe customer {customer.id} for organization {organization_id}")
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer: {str(e)}")
            raise

    @staticmethod
    def get_customer(customer_id: str) -> stripe.Customer:
        """Get customer from Stripe"""
        try:
            return stripe.Customer.retrieve(customer_id)
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving Stripe customer {customer_id}: {str(e)}")
            raise

    @staticmethod
    def create_checkout_session(
        customer_id: str | None,
        price_id: str,
        success_url: str,
        cancel_url: str,
        organization_id: int | None = None,
        mode: str = "subscription",
        metadata: dict[str, Any] | None = None,
    ) -> Any:  # stripe.checkout.Session (using Any to avoid import-time evaluation)
        """
        Create a Stripe Checkout session

        Args:
            customer_id: Existing customer ID (optional, will create if not provided)
            price_id: Stripe Price ID
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment
            organization_id: Organization ID for metadata
            mode: Checkout mode ('subscription' or 'payment')
            metadata: Additional metadata

        Returns:
            Stripe Checkout Session object
        """
        session_data = {
            "mode": mode,
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": metadata or {},
        }

        if customer_id:
            session_data["customer"] = customer_id
        else:
            # Customer will be created during checkout
            session_data["customer_email"] = None  # Will be collected during checkout

        if organization_id:
            session_data["metadata"]["organization_id"] = str(organization_id)

        try:
            session = stripe.checkout.Session.create(**session_data)
            logger.info(
                f"Created Stripe checkout session {session.id} for organization {organization_id}"
            )
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe checkout session: {str(e)}")
            raise

    @staticmethod
    def create_subscription(
        customer_id: str,
        price_id: str,
        organization_id: int | None = None,
        trial_period_days: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:  # stripe.Subscription
        """
        Create a subscription in Stripe

        Args:
            customer_id: Stripe Customer ID
            price_id: Stripe Price ID
            organization_id: Organization ID for metadata
            trial_period_days: Optional trial period in days
            metadata: Additional metadata

        Returns:
            Stripe Subscription object
        """
        subscription_data = {
            "customer": customer_id,
            "items": [{"price": price_id}],
            "metadata": metadata or {},
        }

        if organization_id:
            subscription_data["metadata"]["organization_id"] = str(organization_id)

        if trial_period_days:
            subscription_data["trial_period_days"] = trial_period_days

        try:
            subscription = stripe.Subscription.create(**subscription_data)
            logger.info(
                f"Created Stripe subscription {subscription.id} for organization {organization_id}"
            )
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe subscription: {str(e)}")
            raise

    @staticmethod
    def get_subscription(subscription_id: str) -> stripe.Subscription:
        """Get subscription from Stripe"""
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving Stripe subscription {subscription_id}: {str(e)}")
            raise

    @staticmethod
    def update_subscription(
        subscription_id: str,
        price_id: str | None = None,
        cancel_at_period_end: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:  # stripe.Subscription
        """
        Update a subscription in Stripe

        Args:
            subscription_id: Stripe Subscription ID
            price_id: New Price ID (for plan change)
            cancel_at_period_end: Cancel at end of period
            metadata: Additional metadata

        Returns:
            Updated Stripe Subscription object
        """
        update_data = {}

        if price_id:
            # Get current subscription to update items
            subscription = stripe.Subscription.retrieve(subscription_id)
            update_data["items"] = [{"id": subscription["items"]["data"][0].id, "price": price_id}]
            update_data["proration_behavior"] = "always_invoice"

        if cancel_at_period_end is not None:
            update_data["cancel_at_period_end"] = cancel_at_period_end

        if metadata:
            update_data["metadata"] = metadata

        try:
            subscription = stripe.Subscription.modify(subscription_id, **update_data)
            logger.info(f"Updated Stripe subscription {subscription_id}")
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Error updating Stripe subscription {subscription_id}: {str(e)}")
            raise

    @staticmethod
    def cancel_subscription(
        subscription_id: str, cancel_at_period_end: bool = True
    ) -> Any:  # stripe.Subscription
        """
        Cancel a subscription in Stripe

        Args:
            subscription_id: Stripe Subscription ID
            cancel_at_period_end: If True, cancel at end of period; if False, cancel immediately

        Returns:
            Updated Stripe Subscription object
        """
        try:
            if cancel_at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id, cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)

            logger.info(
                f"Cancelled Stripe subscription {subscription_id} (at_period_end={cancel_at_period_end})"
            )
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling Stripe subscription {subscription_id}: {str(e)}")
            raise

    @staticmethod
    def construct_webhook_event(payload: bytes, sig_header: str) -> Any:  # stripe.Event
        """
        Verify and construct webhook event from Stripe

        Args:
            payload: Raw request body
            sig_header: Stripe signature header

        Returns:
            Stripe Event object
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid payload in Stripe webhook: {str(e)}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature in Stripe webhook: {str(e)}")
            raise


# Create singleton instance
stripe_service = StripeService()
