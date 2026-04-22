"""
Repository for Subscription model
"""

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    """
    Repository for Subscription operations
    """

    def __init__(self, db: AsyncSession, tenant_id: int | None = None):
        super().__init__(db, Subscription, tenant_id=tenant_id)

    async def get_active_subscription(self, organization_id: int) -> Subscription | None:
        """
        Get the active subscription for an organization

        Args:
            organization_id: Organization ID

        Returns:
            Active Subscription instance or None
        """
        query = (
            select(Subscription)
            .where(
                Subscription.organization_id == organization_id,
                Subscription.status.in_(["active", "trialing"]),
            )
            .order_by(desc(Subscription.created_at))
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_stripe_subscription_id(
        self, stripe_subscription_id: str
    ) -> Subscription | None:
        """
        Get subscription by Stripe subscription ID

        Args:
            stripe_subscription_id: Stripe subscription ID

        Returns:
            Subscription instance or None
        """
        query = select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_subscription_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_stripe_customer_id(self, stripe_customer_id: str) -> Subscription | None:
        """
        Get subscription by Stripe customer ID

        Args:
            stripe_customer_id: Stripe customer ID

        Returns:
            Subscription instance or None
        """
        query = (
            select(Subscription)
            .where(Subscription.stripe_customer_id == stripe_customer_id)
            .order_by(desc(Subscription.created_at))
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_latest_subscription(self, organization_id: int) -> Subscription | None:
        """
        Get the latest subscription for an organization (regardless of status)

        Args:
            organization_id: Organization ID

        Returns:
            Latest Subscription instance or None
        """
        query = (
            select(Subscription)
            .where(Subscription.organization_id == organization_id)
            .order_by(desc(Subscription.created_at))
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()
