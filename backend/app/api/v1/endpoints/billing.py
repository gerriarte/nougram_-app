"""
Billing and subscription endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from datetime import timezone

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant import get_tenant_context, TenantContext
from app.core.permission_middleware import require_manage_subscription
from app.core.billing_gateway import get_billing_gateway, BillingGatewayError
from app.core.logging import get_logger
from app.models.user import User
from app.models.subscription import Subscription
from app.repositories.factory import RepositoryFactory
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.billing import (
    CheckoutSessionCreate,
    CheckoutSessionResponse,
    SubscriptionResponse,
    SubscriptionUpdate,
    SubscriptionCancel,
    PlansListResponse,
    PlanInfo,
)

logger = get_logger(__name__)
router = APIRouter()


@router.post("/checkout-session", response_model=CheckoutSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_checkout_session(
    checkout_data: CheckoutSessionCreate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_manage_subscription),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a hosted checkout session for subscription
    
    Only organization owners/admins can create checkout sessions
    """
    gateway = get_billing_gateway()

    # Checkout is optional depending on billing provider.
    if not gateway.supports_checkout:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                f"Hosted checkout is not enabled for provider '{gateway.provider_name}'. "
                "Configure a payment gateway to enable online checkout."
            ),
        )

    # Get price ID for the plan in current provider.
    price_id = gateway.get_price_id(checkout_data.plan, checkout_data.interval)
    
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Price ID not configured for plan {checkout_data.plan} with interval {checkout_data.interval}"
        )
    
    # Get organization
    org_repo = RepositoryFactory.create_organization_repository(db)
    organization = await org_repo.get_by_id(tenant.organization_id)
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Get or create external customer in configured provider.
    customer_id = None
    subscription_repo = RepositoryFactory.create_subscription_repository(db)
    existing_subscription = await subscription_repo.get_latest_subscription(tenant.organization_id)
    
    customer_id = gateway.ensure_customer_id(
        existing_customer_id=existing_subscription.stripe_customer_id if existing_subscription else None,
        email=current_user.email,
        organization_name=organization.name,
        organization_id=tenant.organization_id,
    )
    
    # Create checkout session
    try:
        session = gateway.create_checkout_session(
            customer_id=customer_id,
            price_id=price_id,
            success_url=checkout_data.success_url,
            cancel_url=checkout_data.cancel_url,
            organization_id=tenant.organization_id,
            plan=checkout_data.plan,
            interval=checkout_data.interval,
        )
        
        logger.info(
            f"Created checkout session {session.session_id} for organization {tenant.organization_id}",
            extra={"organization_id": tenant.organization_id, "plan": checkout_data.plan}
        )
        
        return CheckoutSessionResponse(
            session_id=session.session_id,
            url=session.url,
        )
    except BillingGatewayError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current subscription for the organization
    """
    org_repo = RepositoryFactory.create_organization_repository(db)
    organization = await org_repo.get_by_id(tenant.organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    subscription_repo = RepositoryFactory.create_subscription_repository(db)
    subscription = await subscription_repo.get_active_subscription(tenant.organization_id)
    
    if not subscription:
        # Fallback for manual/local billing mode: use organization-level subscription fields.
        return SubscriptionResponse(
            id=0,
            organization_id=tenant.organization_id,
            stripe_subscription_id=None,
            stripe_customer_id=None,
            stripe_price_id=None,
            plan=organization.subscription_plan,
            status=organization.subscription_status,
            current_period_start=None,
            current_period_end=None,
            cancel_at_period_end=False,
            canceled_at=None,
            trial_start=None,
            trial_end=None,
            latest_invoice_id=None,
            default_payment_method=None,
            created_at=organization.created_at or datetime.utcnow(),
            updated_at=organization.updated_at,
        )
    
    return SubscriptionResponse.model_validate(subscription)


@router.put("/subscription", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_data: SubscriptionUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_manage_subscription),
    db: AsyncSession = Depends(get_db)
):
    """
    Update subscription (change plan or cancel at period end)
    
    Only organization owners/admins can update subscriptions
    """
    gateway = get_billing_gateway()
    subscription_repo = RepositoryFactory.create_subscription_repository(db)
    subscription = await subscription_repo.get_active_subscription(tenant.organization_id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    try:
        # If provider has external subscription integration, sync it.
        if subscription.stripe_subscription_id and gateway.provider_name != "manual":
            updated_external = gateway.update_subscription(
                external_subscription_id=subscription.stripe_subscription_id,
                plan=subscription_data.plan,
                interval=subscription_data.interval,
                cancel_at_period_end=subscription_data.cancel_at_period_end,
            )

            subscription.status = updated_external.status
            subscription.current_period_start = updated_external.current_period_start
            subscription.current_period_end = updated_external.current_period_end
            subscription.cancel_at_period_end = updated_external.cancel_at_period_end
            if updated_external.external_price_id:
                subscription.stripe_price_id = updated_external.external_price_id
        elif subscription_data.cancel_at_period_end is not None:
            # Manual/local fallback: update local cancellation intent.
            subscription.cancel_at_period_end = subscription_data.cancel_at_period_end

        if subscription_data.plan:
            subscription.plan = subscription_data.plan
        
        await db.commit()
        await db.refresh(subscription)
        
        logger.info(
            f"Updated subscription {subscription.id} for organization {tenant.organization_id}",
            extra={"organization_id": tenant.organization_id, "plan": subscription.plan}
        )
        
        return SubscriptionResponse.model_validate(subscription)
        
    except (HTTPException, BillingGatewayError):
        raise
    except Exception as e:
        logger.error(f"Error updating subscription: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update subscription: {str(e)}"
        )


@router.post("/subscription/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    cancel_data: SubscriptionCancel,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_manage_subscription),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel subscription (immediately or at period end)
    
    Only organization owners/admins can cancel subscriptions
    """
    gateway = get_billing_gateway()
    subscription_repo = RepositoryFactory.create_subscription_repository(db)
    subscription = await subscription_repo.get_active_subscription(tenant.organization_id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    try:
        # External cancel when available, local fallback otherwise.
        if subscription.stripe_subscription_id and gateway.provider_name != "manual":
            updated_external = gateway.cancel_subscription(
                external_subscription_id=subscription.stripe_subscription_id,
                cancel_immediately=cancel_data.cancel_immediately,
            )
            subscription.status = updated_external.status
            subscription.cancel_at_period_end = updated_external.cancel_at_period_end
            if cancel_data.cancel_immediately:
                subscription.canceled_at = datetime.utcnow()
        else:
            if cancel_data.cancel_immediately:
                subscription.status = "cancelled"
                subscription.canceled_at = datetime.utcnow()
            else:
                subscription.cancel_at_period_end = True
        
        await db.commit()
        await db.refresh(subscription)
        
        logger.info(
            f"Cancelled subscription {subscription.id} for organization {tenant.organization_id}",
            extra={"organization_id": tenant.organization_id, "immediate": cancel_data.cancel_immediately}
        )
        
        return SubscriptionResponse.model_validate(subscription)
        
    except BillingGatewayError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel subscription: {str(e)}"
        )


@router.get("/plans", response_model=PlansListResponse)
async def list_plans(
    current_user: User = Depends(get_current_user)
):
    """
    List available subscription plans
    """
    from app.core.plan_limits import PLAN_INFO
    
    plans = []
    for plan_key, plan_data in PLAN_INFO.items():
        plans.append(PlanInfo(
            name=plan_key,
            display_name=plan_data.get("display_name", plan_key.title()),
            description=plan_data.get("description", ""),
            monthly_price=plan_data.get("monthly_price"),
            yearly_price=plan_data.get("yearly_price"),
            features=plan_data.get("features", []),
            limits=plan_data.get("limits", {})
        ))
    
    return PlansListResponse(plans=plans)


