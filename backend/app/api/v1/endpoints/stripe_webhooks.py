"""
Stripe webhook handler for subscription and payment events
"""
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Optional
import json

from app.core.database import get_db
from app.core.config import settings
from app.core.stripe_service import stripe_service
from app.core.logging import get_logger
from app.models.subscription import Subscription
from app.repositories.factory import RepositoryFactory
from app.repositories.organization_repository import OrganizationRepository

logger = get_logger(__name__)
router = APIRouter()


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    if (settings.PAYMENT_GATEWAY_PROVIDER or "manual").lower() != "stripe":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Stripe webhook is disabled for current payment gateway provider.",
        )

    """
    Handle Stripe webhook events
    
    This endpoint receives events from Stripe and updates the database accordingly.
    Webhook signature verification is performed automatically.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header:
        logger.warning("Stripe webhook received without signature header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    try:
        # Verify and construct webhook event
        event = stripe_service.construct_webhook_event(payload, sig_header)
        
        logger.info(
            f"Received Stripe webhook event: {event['type']}",
            extra={"event_id": event.get("id"), "event_type": event.get("type")}
        )
        
        # Handle event based on type
        if event["type"] == "checkout.session.completed":
            await handle_checkout_session_completed(event, db)
        elif event["type"] == "customer.subscription.created":
            await handle_subscription_created(event, db)
        elif event["type"] == "customer.subscription.updated":
            await handle_subscription_updated(event, db)
        elif event["type"] == "customer.subscription.deleted":
            await handle_subscription_deleted(event, db)
        elif event["type"] == "invoice.payment_succeeded":
            await handle_invoice_payment_succeeded(event, db)
        elif event["type"] == "invoice.payment_failed":
            await handle_invoice_payment_failed(event, db)
        else:
            logger.info(f"Unhandled webhook event type: {event['type']}")
        
        return {"status": "success"}
        
    except ValueError as e:
        logger.error(f"Invalid payload in Stripe webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook"
        )


async def handle_checkout_session_completed(event: dict, db: AsyncSession):
    """Handle checkout.session.completed event"""
    session = event["data"]["object"]
    subscription_id = session.get("subscription")
    customer_id = session.get("customer")
    metadata = session.get("metadata", {})
    organization_id = metadata.get("organization_id")
    
    if not organization_id:
        logger.warning(f"Checkout session {session['id']} completed without organization_id")
        return
    
    organization_id = int(organization_id)
    
    # Get or create subscription
    subscription_repo = RepositoryFactory.create_subscription_repository(db)
    
    if subscription_id:
        # Get subscription from Stripe
        stripe_subscription = stripe_service.get_subscription(subscription_id)
        await sync_subscription_from_stripe(stripe_subscription, organization_id, db)
    
    logger.info(
        f"Checkout session completed for organization {organization_id}",
        extra={"organization_id": organization_id, "subscription_id": subscription_id}
    )


async def handle_subscription_created(event: dict, db: AsyncSession):
    """Handle customer.subscription.created event"""
    stripe_subscription = event["data"]["object"]
    metadata = stripe_subscription.get("metadata", {})
    organization_id = metadata.get("organization_id")
    
    if not organization_id:
        logger.warning(f"Subscription {stripe_subscription['id']} created without organization_id")
        return
    
    organization_id = int(organization_id)
    await sync_subscription_from_stripe(stripe_subscription, organization_id, db)
    
    logger.info(
        f"Subscription created for organization {organization_id}",
        extra={"organization_id": organization_id, "subscription_id": stripe_subscription["id"]}
    )


async def handle_subscription_updated(event: dict, db: AsyncSession):
    """Handle customer.subscription.updated event"""
    stripe_subscription = event["data"]["object"]
    subscription_id = stripe_subscription["id"]
    
    # Find subscription by Stripe ID
    subscription_repo = RepositoryFactory.create_subscription_repository(db)
    subscription = await subscription_repo.get_by_stripe_subscription_id(subscription_id)
    
    if not subscription:
        # Try to get organization_id from metadata
        metadata = stripe_subscription.get("metadata", {})
        organization_id = metadata.get("organization_id")
        if organization_id:
            organization_id = int(organization_id)
            await sync_subscription_from_stripe(stripe_subscription, organization_id, db)
        else:
            logger.warning(f"Subscription {subscription_id} updated but not found in database")
        return
    
    await sync_subscription_from_stripe(stripe_subscription, subscription.organization_id, db)
    
    logger.info(
        f"Subscription updated: {subscription_id}",
        extra={"subscription_id": subscription_id, "status": stripe_subscription["status"]}
    )


async def handle_subscription_deleted(event: dict, db: AsyncSession):
    """Handle customer.subscription.deleted event"""
    stripe_subscription = event["data"]["object"]
    subscription_id = stripe_subscription["id"]
    
    # Find subscription by Stripe ID
    subscription_repo = RepositoryFactory.create_subscription_repository(db)
    subscription = await subscription_repo.get_by_stripe_subscription_id(subscription_id)
    
    if not subscription:
        logger.warning(f"Subscription {subscription_id} deleted but not found in database")
        return
    
    # Mark as cancelled
    subscription.status = "cancelled"
    subscription.canceled_at = datetime.now(timezone.utc)
    
    # Update organization subscription status
    org_repo = RepositoryFactory.create_organization_repository(db)
    await org_repo.update_subscription(
        subscription.organization_id,
        status="cancelled"
    )
    
    await db.commit()
    
    logger.info(
        f"Subscription deleted: {subscription_id}",
        extra={"subscription_id": subscription_id, "organization_id": subscription.organization_id}
    )


async def handle_invoice_payment_succeeded(event: dict, db: AsyncSession):
    """Handle invoice.payment_succeeded event"""
    invoice = event["data"]["object"]
    subscription_id = invoice.get("subscription")
    
    if not subscription_id:
        return
    
    # Update subscription's latest invoice
    subscription_repo = RepositoryFactory.create_subscription_repository(db)
    subscription = await subscription_repo.get_by_stripe_subscription_id(subscription_id)
    
    if subscription:
        subscription.latest_invoice_id = invoice["id"]
        await db.commit()
        
        logger.info(
            f"Invoice payment succeeded for subscription {subscription_id}",
            extra={"subscription_id": subscription_id, "invoice_id": invoice["id"]}
        )


async def handle_invoice_payment_failed(event: dict, db: AsyncSession):
    """Handle invoice.payment_failed event"""
    invoice = event["data"]["object"]
    subscription_id = invoice.get("subscription")
    
    if not subscription_id:
        return
    
    # Update subscription status to past_due
    subscription_repo = RepositoryFactory.create_subscription_repository(db)
    subscription = await subscription_repo.get_by_stripe_subscription_id(subscription_id)
    
    if subscription:
        subscription.status = "past_due"
        subscription.latest_invoice_id = invoice["id"]
        await db.commit()
        
        # Update organization subscription status
        org_repo = RepositoryFactory.create_organization_repository(db)
        await org_repo.update_subscription(
            subscription.organization_id,
            status="past_due"
        )
        
        logger.warning(
            f"Invoice payment failed for subscription {subscription_id}",
            extra={"subscription_id": subscription_id, "invoice_id": invoice["id"]}
        )


async def sync_subscription_from_stripe(
    stripe_subscription: dict,
    organization_id: int,
    db: AsyncSession
):
    """
    Sync subscription data from Stripe to database
    
    Args:
        stripe_subscription: Stripe subscription object
        organization_id: Organization ID
        db: Database session
    """
    subscription_repo = RepositoryFactory.create_subscription_repository(db)
    
    # Check if subscription already exists
    subscription = await subscription_repo.get_by_stripe_subscription_id(stripe_subscription["id"])
    
    if not subscription:
        # Create new subscription
        subscription = Subscription(
            organization_id=organization_id,
            stripe_subscription_id=stripe_subscription["id"],
            stripe_customer_id=stripe_subscription.get("customer"),
            stripe_price_id=stripe_subscription["items"]["data"][0]["price"]["id"] if stripe_subscription["items"]["data"] else None,
            plan=_extract_plan_from_metadata(stripe_subscription) or "free",
            status=stripe_subscription["status"],
            current_period_start=datetime.fromtimestamp(stripe_subscription["current_period_start"], tz=timezone.utc) if stripe_subscription.get("current_period_start") else None,
            current_period_end=datetime.fromtimestamp(stripe_subscription["current_period_end"], tz=timezone.utc) if stripe_subscription.get("current_period_end") else None,
            cancel_at_period_end=stripe_subscription.get("cancel_at_period_end", False),
            trial_start=datetime.fromtimestamp(stripe_subscription["trial_start"], tz=timezone.utc) if stripe_subscription.get("trial_start") else None,
            trial_end=datetime.fromtimestamp(stripe_subscription["trial_end"], tz=timezone.utc) if stripe_subscription.get("trial_end") else None,
            stripe_metadata=stripe_subscription.get("metadata")
        )
        db.add(subscription)
    else:
        # Update existing subscription
        subscription.stripe_customer_id = stripe_subscription.get("customer")
        subscription.stripe_price_id = stripe_subscription["items"]["data"][0]["price"]["id"] if stripe_subscription["items"]["data"] else subscription.stripe_price_id
        subscription.status = stripe_subscription["status"]
        subscription.current_period_start = datetime.fromtimestamp(stripe_subscription["current_period_start"], tz=timezone.utc) if stripe_subscription.get("current_period_start") else None
        subscription.current_period_end = datetime.fromtimestamp(stripe_subscription["current_period_end"], tz=timezone.utc) if stripe_subscription.get("current_period_end") else None
        subscription.cancel_at_period_end = stripe_subscription.get("cancel_at_period_end", False)
        subscription.trial_start = datetime.fromtimestamp(stripe_subscription["trial_start"], tz=timezone.utc) if stripe_subscription.get("trial_start") else None
        subscription.trial_end = datetime.fromtimestamp(stripe_subscription["trial_end"], tz=timezone.utc) if stripe_subscription.get("trial_end") else None
        subscription.stripe_metadata = stripe_subscription.get("metadata")
    
    await db.commit()
    await db.refresh(subscription)
    
    # Update organization subscription status
    org_repo = RepositoryFactory.create_organization_repository(db)
    plan_from_metadata = _extract_plan_from_metadata(stripe_subscription)
    if plan_from_metadata:
        plan = plan_from_metadata
    elif subscription:
        plan = subscription.plan
    else:
        plan = "free"
    
    await org_repo.update_subscription(
        organization_id,
        plan=plan,
        status=stripe_subscription["status"]
    )
    
    # Grant subscription credits when subscription is created or plan is updated
    try:
        from app.services.credit_service import CreditService
        await CreditService.grant_subscription_credits(organization_id, db)
        logger.info(f"Granted subscription credits to organization {organization_id} for plan {plan}")
    except Exception as e:
        # Log error but don't fail webhook processing
        logger.error(f"Error granting subscription credits to organization {organization_id}: {e}", exc_info=True)


def _extract_plan_from_metadata(stripe_subscription: dict) -> Optional[str]:
    """Extract plan from Stripe subscription metadata"""
    metadata = stripe_subscription.get("metadata", {})
    return metadata.get("plan")
