"""
Celery tasks for scheduled operations
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.logging import get_logger
from app.models.organization import Organization
from app.services.credit_service import CreditService

logger = get_logger(__name__)


@celery_app.task(name="app.core.tasks.reset_monthly_credits", bind=True)
def reset_monthly_credits(self):
    """
    Reset monthly credits for all organizations that need it.

    This task runs daily and checks all organizations to see if their
    next_reset_at date has passed. If so, it grants new monthly credits.

    This is a synchronous wrapper around the async function.
    """
    import asyncio

    # Run the async function
    asyncio.run(_reset_monthly_credits_async())


async def _reset_monthly_credits_async():
    """
    Async function to reset monthly credits for organizations

    This function:
    1. Gets all active organizations
    2. For each organization, checks if next_reset_at <= now()
    3. If yes, calls CreditService.grant_subscription_credits()
    """
    # Create engine for this task execution
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db:
            try:
                # Get all active organizations
                result = await db.execute(
                    select(Organization).where(Organization.subscription_status == "active")
                )
                organizations = result.scalars().all()

                logger.info(f"Checking {len(organizations)} organizations for monthly credit reset")

                reset_count = 0
                error_count = 0
                now = datetime.utcnow()

                for org in organizations:
                    try:
                        # Get credit account
                        account = await CreditService.get_or_create_credit_account(
                            organization_id=org.id, db=db
                        )

                        # Check if reset is needed
                        if account.next_reset_at is None:
                            # First time setup - grant initial credits
                            logger.info(f"First-time credit grant for organization {org.id}")
                            await CreditService.grant_subscription_credits(
                                organization_id=org.id, db=db
                            )
                            reset_count += 1
                        elif account.next_reset_at <= now:
                            # Time for monthly reset
                            logger.info(
                                f"Resetting monthly credits for organization {org.id} "
                                f"(next_reset_at: {account.next_reset_at})"
                            )
                            await CreditService.grant_subscription_credits(
                                organization_id=org.id, db=db
                            )
                            reset_count += 1

                    except Exception as e:
                        error_count += 1
                        logger.error(
                            f"Error resetting credits for organization {org.id}",
                            error=str(e),
                            exc_info=True,
                        )
                        # Continue with next organization
                        continue

                logger.info(
                    f"Monthly credit reset completed: {reset_count} resets, {error_count} errors"
                )

            except Exception as e:
                logger.error("Error in monthly credit reset task", error=str(e), exc_info=True)
                raise
    finally:
        await engine.dispose()
