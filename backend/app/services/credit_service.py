"""
Credit Service for managing organization credits
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.credit_account import CreditAccount
from app.models.credit_transaction import CreditTransaction
from app.models.organization import Organization
from app.repositories.credit_account_repository import CreditAccountRepository
from app.repositories.credit_transaction_repository import CreditTransactionRepository
from app.core.plan_limits import get_plan_limit, is_unlimited
from app.core.logging import get_logger

logger = get_logger(__name__)


class CreditService:
    """
    Service for managing organization credits
    """
    
    # Transaction types
    TRANSACTION_TYPE_SUBSCRIPTION_GRANT = "subscription_grant"
    TRANSACTION_TYPE_MANUAL_ADJUSTMENT = "manual_adjustment"
    TRANSACTION_TYPE_CONSUMPTION = "consumption"
    TRANSACTION_TYPE_REFUND = "refund"
    SUBSCRIPTION_GRANT_DEDUP_WINDOW_SECONDS = 300
    
    @staticmethod
    async def get_or_create_credit_account(
        organization_id: int,
        db: AsyncSession
    ) -> CreditAccount:
        """
        Get or create a credit account for an organization
        
        Args:
            organization_id: Organization ID
            db: Database session
            
        Returns:
            CreditAccount instance
        """
        repo = CreditAccountRepository(db)
        account = await repo.get_by_organization_id(organization_id)
        
        if account is None:
            # Get organization to determine plan
            from sqlalchemy import select
            result = await db.execute(
                select(Organization).where(Organization.id == organization_id)
            )
            org = result.scalar_one_or_none()
            
            if org is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Organization {organization_id} not found"
                )
            
            # Get credits per month from plan
            credits_per_month = get_plan_limit(org.subscription_plan, "credits_per_month")
            if is_unlimited(credits_per_month):
                credits_per_month = None  # NULL means unlimited
            
            account = await repo.create_for_organization(
                organization_id=organization_id,
                credits_per_month=credits_per_month,
                auto_commit=False,
            )
            await db.commit()
            await db.refresh(account)
            
            logger.info(f"Created credit account for organization {organization_id} with {credits_per_month} credits/month")
        
        return account
    
    @staticmethod
    async def get_credit_balance(
        organization_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get credit balance information for an organization
        
        Args:
            organization_id: Organization ID
            db: Database session
            
        Returns:
            Dictionary with credit balance information
        """
        account = await CreditService.get_or_create_credit_account(organization_id, db)
        
        return {
            "organization_id": organization_id,
            "credits_available": account.credits_available,
            "credits_used_total": account.credits_used_total,
            "credits_used_this_month": account.credits_used_this_month,
            "credits_per_month": account.credits_per_month,
            "manual_credits_bonus": account.manual_credits_bonus,
            "last_reset_at": account.last_reset_at.isoformat() if account.last_reset_at else None,
            "next_reset_at": account.next_reset_at.isoformat() if account.next_reset_at else None,
            "is_unlimited": account.credits_per_month is None
        }
    
    @staticmethod
    async def validate_and_consume_credits(
        organization_id: int,
        amount: int,
        user_id: Optional[int],
        reason: str,
        db: AsyncSession,
        reference_id: Optional[int] = None
    ) -> bool:
        """
        Validate that organization has enough credits and consume them
        
        Args:
            organization_id: Organization ID
            amount: Number of credits to consume (must be positive)
            user_id: ID of user consuming credits (for audit)
            reason: Reason for consumption
            db: Database session
            reference_id: Optional reference ID (e.g., quote ID)
            
        Returns:
            True if credits were consumed successfully
            
        Raises:
            HTTPException 402: If insufficient credits
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        account = await CreditService.get_or_create_credit_account(organization_id, db)
        
        # Check if unlimited
        if account.credits_per_month is None:
            logger.info(f"Organization {organization_id} has unlimited credits, skipping consumption")
            return True
        
        # Check if sufficient credits
        if account.credits_available < amount:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    f"Insufficient credits. Available: {account.credits_available}, "
                    f"Required: {amount}. Please upgrade your plan or contact support."
                )
            )
        
        # Consume credits
        account.credits_available -= amount
        account.credits_used_total += amount
        account.credits_used_this_month += amount
        
        # Create transaction record
        transaction_repo = CreditTransactionRepository(db)
        await transaction_repo.create_transaction(
            organization_id=organization_id,
            transaction_type=CreditService.TRANSACTION_TYPE_CONSUMPTION,
            amount=-amount,  # Negative for consumption
            reason=reason,
            reference_id=reference_id,
            performed_by=user_id,
            auto_commit=False,
        )
        
        await db.commit()
        await db.refresh(account)
        
        logger.info(f"Consumed {amount} credits for organization {organization_id}. Remaining: {account.credits_available}")
        
        return True
    
    @staticmethod
    async def grant_subscription_credits(
        organization_id: int,
        db: AsyncSession,
        force: bool = False,
    ) -> None:
        """
        Grant monthly subscription credits to an organization
        This is called during monthly reset or when subscription is created/updated
        
        Args:
            organization_id: Organization ID
            db: Database session
        """
        from sqlalchemy import select
        
        # Get organization to determine plan
        result = await db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = result.scalar_one_or_none()
        
        if org is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization {organization_id} not found"
            )
        
        account = await CreditService.get_or_create_credit_account(organization_id, db)
        transaction_repo = CreditTransactionRepository(db)
        now = datetime.utcnow()

        # Avoid accidental double grants from bursty events (e.g., overlapping Stripe webhooks).
        if not force:
            latest_grant = await transaction_repo.get_latest_by_type(
                organization_id=organization_id,
                transaction_type=CreditService.TRANSACTION_TYPE_SUBSCRIPTION_GRANT,
            )
            if latest_grant and latest_grant.created_at:
                elapsed = (now - latest_grant.created_at.replace(tzinfo=None)).total_seconds()
                if elapsed <= CreditService.SUBSCRIPTION_GRANT_DEDUP_WINDOW_SECONDS:
                    logger.warning(
                        f"Skipping duplicate subscription grant for organization {organization_id} "
                        f"(elapsed {elapsed:.1f}s)"
                    )
                    return
        
        # Get credits per month from plan
        credits_per_month = get_plan_limit(org.subscription_plan, "credits_per_month")
        
        # Update credits_per_month in account if it changed
        if is_unlimited(credits_per_month):
            account.credits_per_month = None  # NULL means unlimited
        else:
            account.credits_per_month = credits_per_month
            # Reset monthly usage counter
            account.credits_used_this_month = 0
            # Grant new credits
            account.credits_available += credits_per_month
            
            # Create transaction record
            await transaction_repo.create_transaction(
                organization_id=organization_id,
                transaction_type=CreditService.TRANSACTION_TYPE_SUBSCRIPTION_GRANT,
                amount=credits_per_month,
                reason=f"Monthly subscription grant for {org.subscription_plan} plan",
                performed_by=None,
                auto_commit=False,
            )
            
            logger.info(f"Granted {credits_per_month} credits to organization {organization_id} ({org.subscription_plan} plan)")
        
        # Update reset timestamps
        account.last_reset_at = now
        
        # Calculate next reset (one month from now)
        if account.next_reset_at is None:
            # First time, set next reset to one month from now
            account.next_reset_at = now + timedelta(days=30)
        else:
            # Add one month to next reset date
            account.next_reset_at = account.next_reset_at + timedelta(days=30)
        
        await db.commit()
        await db.refresh(account)
    
    @staticmethod
    async def grant_manual_credits(
        organization_id: int,
        amount: int,
        granted_by: int,
        reason: str,
        db: AsyncSession
    ) -> None:
        """
        Grant manual credits to an organization (admin function)
        
        Args:
            organization_id: Organization ID
            amount: Number of credits to grant (must be positive)
            granted_by: ID of user granting credits (admin)
            reason: Reason for granting credits
            db: Database session
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        account = await CreditService.get_or_create_credit_account(organization_id, db)
        
        # Grant credits
        account.credits_available += amount
        account.manual_credits_bonus += amount
        account.manual_credits_last_assigned_at = datetime.utcnow()
        account.manual_credits_assigned_by = granted_by
        
        # Create transaction record
        transaction_repo = CreditTransactionRepository(db)
        await transaction_repo.create_transaction(
            organization_id=organization_id,
            transaction_type=CreditService.TRANSACTION_TYPE_MANUAL_ADJUSTMENT,
            amount=amount,
            reason=reason,
            performed_by=granted_by,
            auto_commit=False,
        )
        
        await db.commit()
        await db.refresh(account)
        
        logger.info(f"Granted {amount} manual credits to organization {organization_id} by user {granted_by}")
    
    @staticmethod
    async def refund_credits(
        organization_id: int,
        amount: int,
        reason: str,
        db: AsyncSession,
        reference_id: Optional[int] = None
    ) -> None:
        """
        Refund credits to an organization
        
        Args:
            organization_id: Organization ID
            amount: Number of credits to refund (must be positive)
            reason: Reason for refund
            db: Database session
            reference_id: Optional reference ID (e.g., quote ID that was cancelled)
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        account = await CreditService.get_or_create_credit_account(organization_id, db)
        
        # Refund credits
        account.credits_available += amount
        
        # Create transaction record
        transaction_repo = CreditTransactionRepository(db)
        await transaction_repo.create_transaction(
            organization_id=organization_id,
            transaction_type=CreditService.TRANSACTION_TYPE_REFUND,
            amount=amount,
            reason=reason,
            reference_id=reference_id,
            performed_by=None,
            auto_commit=False,
        )
        
        await db.commit()
        await db.refresh(account)
        
        logger.info(f"Refunded {amount} credits to organization {organization_id}")






