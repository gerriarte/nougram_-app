"""
Unit tests for credit service
"""

import pytest
from fastapi import HTTPException, status

from app.models.credit_transaction import CreditTransaction
from app.services.credit_service import CreditService


@pytest.mark.unit
class TestCreditService:
    """Tests for CreditService"""

    async def test_get_or_create_credit_account_new(self, db_session, test_organization):
        """Test creating a new credit account"""
        account = await CreditService.get_or_create_credit_account(test_organization.id, db_session)

        assert account is not None
        assert account.organization_id == test_organization.id
        assert account.credits_available == 0
        assert account.credits_used_total == 0
        assert account.credits_used_this_month == 0

    async def test_get_or_create_credit_account_existing(self, db_session, test_organization):
        """Test getting existing credit account"""
        # Create account first
        account1 = await CreditService.get_or_create_credit_account(
            test_organization.id, db_session
        )
        account1.credits_available = 100
        db_session.add(account1)
        await db_session.commit()

        # Get existing account
        account2 = await CreditService.get_or_create_credit_account(
            test_organization.id, db_session
        )

        assert account2.id == account1.id
        assert account2.credits_available == 100

    async def test_get_credit_balance(self, db_session, test_organization):
        """Test getting credit balance"""
        # Create account with credits
        account = await CreditService.get_or_create_credit_account(test_organization.id, db_session)
        account.credits_available = 150
        account.credits_used_total = 50
        account.credits_used_this_month = 25
        account.credits_per_month = 200
        db_session.add(account)
        await db_session.commit()

        balance = await CreditService.get_credit_balance(test_organization.id, db_session)

        assert balance["organization_id"] == test_organization.id
        assert balance["credits_available"] == 150
        assert balance["credits_used_total"] == 50
        assert balance["credits_used_this_month"] == 25
        assert balance["credits_per_month"] == 200
        assert balance["is_unlimited"] is False

    async def test_get_credit_balance_unlimited(self, db_session, test_organization):
        """Test getting credit balance for unlimited plan"""
        # Create account with unlimited credits
        account = await CreditService.get_or_create_credit_account(test_organization.id, db_session)
        account.credits_per_month = None  # Unlimited
        db_session.add(account)
        await db_session.commit()

        balance = await CreditService.get_credit_balance(test_organization.id, db_session)

        assert balance["is_unlimited"] is True
        assert balance["credits_per_month"] is None

    async def test_validate_and_consume_credits_success(
        self, db_session, test_organization, test_user
    ):
        """Test successful credit consumption"""
        # Create account with credits (ensure it's not unlimited)
        account = await CreditService.get_or_create_credit_account(test_organization.id, db_session)
        # Reset account to clean state
        account.credits_available = 100
        account.credits_per_month = 200  # Ensure not unlimited
        account.credits_used_total = 0  # Reset used credits
        account.credits_used_this_month = 0  # Reset monthly usage
        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)

        result = await CreditService.validate_and_consume_credits(
            test_organization.id, 50, test_user.id, "Test consumption", db_session
        )

        assert result is True
        # Get fresh account after consumption
        from app.repositories.credit_account_repository import CreditAccountRepository

        account_repo = CreditAccountRepository(db_session)
        updated_account = await account_repo.get_by_organization_id(test_organization.id)
        assert updated_account is not None
        assert updated_account.credits_available == 50
        assert updated_account.credits_used_total == 50
        assert updated_account.credits_used_this_month == 50

    async def test_validate_and_consume_credits_insufficient(
        self, db_session, test_organization, test_user
    ):
        """Test credit consumption with insufficient credits"""
        # Create account with limited credits (ensure it's not unlimited)
        account = await CreditService.get_or_create_credit_account(test_organization.id, db_session)
        account.credits_available = 30
        account.credits_per_month = 100  # Ensure not unlimited
        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)

        with pytest.raises(HTTPException) as exc_info:
            await CreditService.validate_and_consume_credits(
                test_organization.id,
                50,  # More than available
                test_user.id,
                "Test consumption",
                db_session,
            )

        assert exc_info.value.status_code == status.HTTP_402_PAYMENT_REQUIRED

    async def test_validate_and_consume_credits_unlimited(
        self, db_session, test_organization, test_user
    ):
        """Test credit consumption for unlimited plan"""
        # Create account with unlimited credits
        account = await CreditService.get_or_create_credit_account(test_organization.id, db_session)
        account.credits_per_month = None  # Unlimited
        account.credits_available = 0
        db_session.add(account)
        await db_session.commit()

        result = await CreditService.validate_and_consume_credits(
            test_organization.id,
            1000,  # Large amount
            test_user.id,
            "Test consumption",
            db_session,
        )

        # Should succeed without consuming (unlimited)
        assert result is True
        await db_session.refresh(account)
        assert account.credits_available == 0  # Not changed for unlimited

    async def test_validate_and_consume_credits_invalid_amount(
        self, db_session, test_organization, test_user
    ):
        """Test credit consumption with invalid amount"""
        with pytest.raises(ValueError, match="Amount must be positive"):
            await CreditService.validate_and_consume_credits(
                test_organization.id,
                0,  # Invalid
                test_user.id,
                "Test consumption",
                db_session,
            )

        with pytest.raises(ValueError, match="Amount must be positive"):
            await CreditService.validate_and_consume_credits(
                test_organization.id,
                -10,  # Invalid
                test_user.id,
                "Test consumption",
                db_session,
            )

    async def test_grant_subscription_credits(self, db_session, test_organization):
        """Test granting subscription credits"""
        # Set organization plan
        test_organization.subscription_plan = "starter"  # Assuming starter has 100 credits/month
        db_session.add(test_organization)
        await db_session.commit()

        await CreditService.grant_subscription_credits(test_organization.id, db_session)

        account = await CreditService.get_or_create_credit_account(test_organization.id, db_session)

        # Credits should be granted (exact amount depends on plan limits)
        assert account.credits_available > 0
        assert account.last_reset_at is not None
        assert account.next_reset_at is not None

    async def test_grant_manual_credits(self, db_session, test_organization, test_admin_user):
        """Test granting manual credits"""
        account = await CreditService.get_or_create_credit_account(test_organization.id, db_session)
        initial_credits = account.credits_available
        initial_bonus = account.manual_credits_bonus
        db_session.add(account)
        await db_session.commit()

        await CreditService.grant_manual_credits(
            test_organization.id, 50, test_admin_user.id, "Test manual grant", db_session
        )

        await db_session.refresh(account)
        assert account.credits_available == initial_credits + 50
        assert account.manual_credits_bonus == initial_bonus + 50
        assert account.manual_credits_assigned_by == test_admin_user.id

    async def test_grant_manual_credits_invalid_amount(
        self, db_session, test_organization, test_admin_user
    ):
        """Test granting manual credits with invalid amount"""
        with pytest.raises(ValueError, match="Amount must be positive"):
            await CreditService.grant_manual_credits(
                test_organization.id, 0, test_admin_user.id, "Test", db_session
            )

    async def test_refund_credits(self, db_session, test_organization):
        """Test refunding credits"""
        account = await CreditService.get_or_create_credit_account(test_organization.id, db_session)
        account.credits_available = 50
        db_session.add(account)
        await db_session.commit()

        await CreditService.refund_credits(
            test_organization.id, 25, "Test refund", db_session, reference_id=123
        )

        await db_session.refresh(account)
        assert account.credits_available == 75  # 50 + 25

    async def test_refund_credits_invalid_amount(self, db_session, test_organization):
        """Test refunding credits with invalid amount"""
        with pytest.raises(ValueError, match="Amount must be positive"):
            await CreditService.refund_credits(test_organization.id, -10, "Test", db_session)

    async def test_credit_transaction_creation(self, db_session, test_organization, test_user):
        """Test that credit transactions are created"""
        account = await CreditService.get_or_create_credit_account(test_organization.id, db_session)
        account.credits_available = 100
        db_session.add(account)
        await db_session.commit()

        # Consume credits
        await CreditService.validate_and_consume_credits(
            test_organization.id, 30, test_user.id, "Test transaction", db_session, reference_id=456
        )

        # Check transaction was created
        from sqlalchemy import select

        result = await db_session.execute(
            select(CreditTransaction).where(
                CreditTransaction.organization_id == test_organization.id
            )
        )
        transactions = result.scalars().all()

        assert len(transactions) > 0
        transaction = transactions[-1]  # Get last transaction
        assert transaction.transaction_type == CreditService.TRANSACTION_TYPE_CONSUMPTION
        assert transaction.amount == -30
        assert transaction.reason == "Test transaction"
        assert transaction.reference_id == 456
        assert transaction.performed_by == test_user.id
