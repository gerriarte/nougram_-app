"""
Integration tests for credit system

Tests cover:
1. Credit account creation and initialization
2. Subscription credit grants (automatic)
3. Credit consumption based on user roles
4. Manual credit grants (admin)
5. Credit refunds
6. Transaction history
7. Credit balance queries
8. Insufficient credits validation
9. Unlimited credits (enterprise plan)
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.user import User
from app.models.organization import Organization
from app.core.security import get_password_hash
from app.services.credit_service import CreditService
from app.repositories.credit_transaction_repository import CreditTransactionRepository


@pytest.fixture
async def org_free(db_session: AsyncSession) -> Organization:
    """Create organization with free plan"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    org = Organization(
        name="Test Free Org",
        slug=f"test-free-{unique_id}",
        subscription_plan="free",
        subscription_status="active"
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def org_starter(db_session: AsyncSession) -> Organization:
    """Create organization with starter plan"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    org = Organization(
        name="Test Starter Org",
        slug=f"test-starter-{unique_id}",
        subscription_plan="starter",
        subscription_status="active"
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def org_professional(db_session: AsyncSession) -> Organization:
    """Create organization with professional plan"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    org = Organization(
        name="Test Professional Org",
        slug=f"test-professional-{unique_id}",
        subscription_plan="professional",
        subscription_status="active"
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def org_enterprise(db_session: AsyncSession) -> Organization:
    """Create organization with enterprise plan (unlimited credits)"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    org = Organization(
        name="Test Enterprise Org",
        slug=f"test-enterprise-{unique_id}",
        subscription_plan="enterprise",
        subscription_status="active"
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def owner_user(db_session: AsyncSession, org_free: Organization) -> User:
    """Create owner user"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"owner-{unique_id}@test.com",
        full_name="Owner User",
        hashed_password=get_password_hash("password123"),
        role="owner",
        role_type="tenant",
        organization_id=org_free.id
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_financiero_user(db_session: AsyncSession, org_free: Organization) -> User:
    """Create admin_financiero user"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"admin-fin-{unique_id}@test.com",
        full_name="Admin Financiero",
        hashed_password=get_password_hash("password123"),
        role="admin_financiero",
        role_type="tenant",
        organization_id=org_free.id
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def product_manager_user(db_session: AsyncSession, org_free: Organization) -> User:
    """Create product_manager user"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"pm-{unique_id}@test.com",
        full_name="Product Manager",
        hashed_password=get_password_hash("password123"),
        role="product_manager",
        role_type="tenant",
        organization_id=org_free.id
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def super_admin_user(db_session: AsyncSession) -> User:
    """Create super_admin user"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"superadmin-{unique_id}@test.com",
        full_name="Super Admin",
        hashed_password=get_password_hash("password123"),
        role="super_admin",
        role_type="support",
        organization_id=None
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.integration
class TestCreditAccountCreation:
    """Tests for credit account creation"""

    async def test_get_or_create_credit_account_creates_new(self, db_session: AsyncSession, org_free: Organization):
        """Test that get_or_create_credit_account creates a new account if none exists"""
        account = await CreditService.get_or_create_credit_account(org_free.id, db_session)

        assert account is not None
        assert account.organization_id == org_free.id
        assert account.credits_available == 0  # Initially 0, needs grant
        assert account.credits_per_month == 10  # Free plan: 10 credits/month

    async def test_get_or_create_credit_account_returns_existing(self, db_session: AsyncSession, org_free: Organization):
        """Test that get_or_create_credit_account returns existing account"""
        account1 = await CreditService.get_or_create_credit_account(org_free.id, db_session)
        account2 = await CreditService.get_or_create_credit_account(org_free.id, db_session)

        assert account1.id == account2.id
        assert account1.organization_id == account2.organization_id

    async def test_credit_account_credits_per_month_by_plan(self, db_session: AsyncSession):
        """Test that credit accounts have correct credits_per_month based on plan"""
        import uuid

        # Test free plan
        org_free = Organization(
            name="Free Org",
            slug=f"free-{uuid.uuid4().hex[:8]}",
            subscription_plan="free",
            subscription_status="active"
        )
        db_session.add(org_free)
        await db_session.commit()
        await db_session.refresh(org_free)

        account_free = await CreditService.get_or_create_credit_account(org_free.id, db_session)
        assert account_free.credits_per_month == 10

        # Test starter plan
        org_starter = Organization(
            name="Starter Org",
            slug=f"starter-{uuid.uuid4().hex[:8]}",
            subscription_plan="starter",
            subscription_status="active"
        )
        db_session.add(org_starter)
        await db_session.commit()
        await db_session.refresh(org_starter)

        account_starter = await CreditService.get_or_create_credit_account(org_starter.id, db_session)
        assert account_starter.credits_per_month == 100

        # Test professional plan
        org_pro = Organization(
            name="Pro Org",
            slug=f"pro-{uuid.uuid4().hex[:8]}",
            subscription_plan="professional",
            subscription_status="active"
        )
        db_session.add(org_pro)
        await db_session.commit()
        await db_session.refresh(org_pro)

        account_pro = await CreditService.get_or_create_credit_account(org_pro.id, db_session)
        assert account_pro.credits_per_month == 500

        # Test enterprise plan (unlimited)
        org_enterprise = Organization(
            name="Enterprise Org",
            slug=f"enterprise-{uuid.uuid4().hex[:8]}",
            subscription_plan="enterprise",
            subscription_status="active"
        )
        db_session.add(org_enterprise)
        await db_session.commit()
        await db_session.refresh(org_enterprise)

        account_enterprise = await CreditService.get_or_create_credit_account(org_enterprise.id, db_session)
        assert account_enterprise.credits_per_month is None  # None = unlimited


@pytest.mark.integration
class TestSubscriptionCreditGrants:
    """Tests for subscription credit grants"""

    async def test_grant_subscription_credits_grants_correct_amount(self, db_session: AsyncSession, org_starter: Organization):
        """Test that grant_subscription_credits grants correct amount for plan"""
        await CreditService.grant_subscription_credits(org_starter.id, db_session)

        balance = await CreditService.get_credit_balance(org_starter.id, db_session)
        assert balance["credits_available"] == 100  # Starter plan: 100 credits
        assert balance["credits_per_month"] == 100

    async def test_grant_subscription_credits_resets_monthly_counter(self, db_session: AsyncSession, org_free: Organization):
        """Test that grant_subscription_credits resets credits_used_this_month and adds new credits"""
        # First, create account and grant credits
        await CreditService.grant_subscription_credits(org_free.id, db_session)

        # Verify initial state
        balance_before = await CreditService.get_credit_balance(org_free.id, db_session)
        assert balance_before["credits_available"] == 10
        assert balance_before["credits_used_this_month"] == 0

        # Consume some credits
        await CreditService.validate_and_consume_credits(
            organization_id=org_free.id,
            amount=5,
            user_id=None,
            reason="Test consumption",
            db=db_session
        )

        # Verify consumption
        balance_after_consume = await CreditService.get_credit_balance(org_free.id, db_session)
        assert balance_after_consume["credits_available"] == 5
        assert balance_after_consume["credits_used_this_month"] == 5

        # Grant again (simulating monthly reset; force bypasses webhook dedup window)
        await CreditService.grant_subscription_credits(org_free.id, db_session, force=True)

        balance = await CreditService.get_credit_balance(org_free.id, db_session)
        assert balance["credits_used_this_month"] == 0  # Should be reset
        # Should have remaining credits (5) + new monthly allocation (10) = 15
        assert balance["credits_available"] == 15

    async def test_grant_subscription_credits_creates_transaction(self, db_session: AsyncSession, org_free: Organization):
        """Test that grant_subscription_credits creates a transaction record"""
        await CreditService.grant_subscription_credits(org_free.id, db_session)

        transaction_repo = CreditTransactionRepository(db_session)
        transactions = await transaction_repo.get_by_organization_id(org_free.id)

        assert len(transactions) == 1
        assert transactions[0].transaction_type == CreditService.TRANSACTION_TYPE_SUBSCRIPTION_GRANT
        assert transactions[0].amount == 10
        assert transactions[0].organization_id == org_free.id


@pytest.mark.integration
class TestCreditConsumption:
    """Tests for credit consumption"""

    async def test_consume_credits_decreases_available(self, db_session: AsyncSession, org_free: Organization):
        """Test that consuming credits decreases available balance"""
        # Grant credits first
        await CreditService.grant_subscription_credits(org_free.id, db_session)

        # Consume credits
        await CreditService.validate_and_consume_credits(
            organization_id=org_free.id,
            amount=3,
            user_id=None,
            reason="Test consumption",
            db=db_session
        )

        balance = await CreditService.get_credit_balance(org_free.id, db_session)
        assert balance["credits_available"] == 7  # 10 - 3
        assert balance["credits_used_total"] == 3
        assert balance["credits_used_this_month"] == 3

    async def test_consume_credits_creates_transaction(self, db_session: AsyncSession, org_free: Organization, product_manager_user: User):
        """Test that consuming credits creates a transaction record"""
        # Grant credits first
        await CreditService.grant_subscription_credits(org_free.id, db_session)

        # Consume credits
        await CreditService.validate_and_consume_credits(
            organization_id=org_free.id,
            amount=2,
            user_id=product_manager_user.id,
            reason="Creating project",
            db=db_session,
            reference_id=123
        )

        transaction_repo = CreditTransactionRepository(db_session)
        transactions = await transaction_repo.get_by_organization_id(org_free.id)

        # Should have 2 transactions: grant + consumption
        consumption_txns = [t for t in transactions if t.transaction_type == CreditService.TRANSACTION_TYPE_CONSUMPTION]
        assert len(consumption_txns) == 1
        assert consumption_txns[0].amount == -2  # Negative for consumption
        assert consumption_txns[0].performed_by == product_manager_user.id
        assert consumption_txns[0].reference_id == 123
        assert consumption_txns[0].reason == "Creating project"

    async def test_consume_credits_insufficient_raises_exception(self, db_session: AsyncSession, org_free: Organization):
        """Test that consuming more credits than available raises HTTPException 402"""
        # Grant credits first
        await CreditService.grant_subscription_credits(org_free.id, db_session)

        # Try to consume more than available
        with pytest.raises(HTTPException) as exc_info:
            await CreditService.validate_and_consume_credits(
                organization_id=org_free.id,
                amount=20,  # More than 10 available
                user_id=None,
                reason="Test overconsumption",
                db=db_session
            )

        assert exc_info.value.status_code == 402
        assert "Insufficient credits" in exc_info.value.detail

    async def test_unlimited_credits_do_not_consume(self, db_session: AsyncSession, org_enterprise: Organization):
        """Test that organizations with unlimited credits do not consume credits"""
        # Enterprise plan should have unlimited credits
        account = await CreditService.get_or_create_credit_account(org_enterprise.id, db_session)
        assert account.credits_per_month is None  # None = unlimited

        # Try to consume (should succeed without actually consuming)
        result = await CreditService.validate_and_consume_credits(
            organization_id=org_enterprise.id,
            amount=1000,  # Large amount
            user_id=None,
            reason="Test unlimited",
            db=db_session
        )

        assert result is True

        # Balance should be unchanged (unlimited accounts don't track consumption)
        balance = await CreditService.get_credit_balance(org_enterprise.id, db_session)
        assert balance["is_unlimited"] is True


@pytest.mark.integration
class TestManualCreditGrants:
    """Tests for manual credit grants (admin)"""

    async def test_grant_manual_credits_increases_available(self, db_session: AsyncSession, org_free: Organization, super_admin_user: User):
        """Test that granting manual credits increases available balance"""
        # Grant subscription credits first
        await CreditService.grant_subscription_credits(org_free.id, db_session)

        # Grant manual credits
        await CreditService.grant_manual_credits(
            organization_id=org_free.id,
            amount=50,
            granted_by=super_admin_user.id,
            reason="Bono especial",
            db=db_session
        )

        balance = await CreditService.get_credit_balance(org_free.id, db_session)
        assert balance["credits_available"] == 60  # 10 (subscription) + 50 (manual)
        assert balance["manual_credits_bonus"] == 50

    async def test_grant_manual_credits_creates_transaction(self, db_session: AsyncSession, org_free: Organization, super_admin_user: User):
        """Test that granting manual credits creates a transaction record"""
        await CreditService.grant_manual_credits(
            organization_id=org_free.id,
            amount=25,
            granted_by=super_admin_user.id,
            reason="Customer bonus",
            db=db_session
        )

        transaction_repo = CreditTransactionRepository(db_session)
        transactions = await transaction_repo.get_by_organization_id(org_free.id)

        manual_txns = [t for t in transactions if t.transaction_type == CreditService.TRANSACTION_TYPE_MANUAL_ADJUSTMENT]
        assert len(manual_txns) == 1
        assert manual_txns[0].amount == 25
        assert manual_txns[0].performed_by == super_admin_user.id
        assert manual_txns[0].reason == "Customer bonus"


@pytest.mark.integration
class TestCreditRefunds:
    """Tests for credit refunds"""

    async def test_refund_credits_increases_available(self, db_session: AsyncSession, org_free: Organization):
        """Test that refunding credits increases available balance"""
        # Grant and consume credits first
        await CreditService.grant_subscription_credits(org_free.id, db_session)
        await CreditService.validate_and_consume_credits(
            organization_id=org_free.id,
            amount=5,
            user_id=None,
            reason="Test",
            db=db_session
        )

        # Refund credits
        await CreditService.refund_credits(
            organization_id=org_free.id,
            amount=3,
            reason="Cancelled project",
            db=db_session,
            reference_id=123
        )

        balance = await CreditService.get_credit_balance(org_free.id, db_session)
        assert balance["credits_available"] == 8  # 10 - 5 + 3

    async def test_refund_credits_creates_transaction(self, db_session: AsyncSession, org_free: Organization):
        """Test that refunding credits creates a transaction record"""
        await CreditService.grant_subscription_credits(org_free.id, db_session)

        await CreditService.refund_credits(
            organization_id=org_free.id,
            amount=5,
            reason="Project cancellation",
            db=db_session,
            reference_id=456
        )

        transaction_repo = CreditTransactionRepository(db_session)
        transactions = await transaction_repo.get_by_organization_id(org_free.id)

        refund_txns = [t for t in transactions if t.transaction_type == CreditService.TRANSACTION_TYPE_REFUND]
        assert len(refund_txns) == 1
        assert refund_txns[0].amount == 5
        assert refund_txns[0].reference_id == 456
        assert refund_txns[0].reason == "Project cancellation"


@pytest.mark.integration
class TestCreditBalance:
    """Tests for credit balance queries"""

    async def test_get_credit_balance_returns_correct_info(self, db_session: AsyncSession, org_starter: Organization):
        """Test that get_credit_balance returns correct information"""
        # Grant credits first
        await CreditService.grant_subscription_credits(org_starter.id, db_session)

        # Consume some credits
        await CreditService.validate_and_consume_credits(
            organization_id=org_starter.id,
            amount=30,
            user_id=None,
            reason="Test",
            db=db_session
        )

        balance = await CreditService.get_credit_balance(org_starter.id, db_session)

        assert balance["organization_id"] == org_starter.id
        assert balance["credits_available"] == 70  # 100 - 30
        assert balance["credits_used_total"] == 30
        assert balance["credits_used_this_month"] == 30
        assert balance["credits_per_month"] == 100
        assert balance["is_unlimited"] is False


@pytest.mark.integration
class TestCreditTransactionsHistory:
    """Tests for credit transaction history"""

    async def test_transaction_history_includes_all_transactions(self, db_session: AsyncSession, org_free: Organization, super_admin_user: User):
        """Test that transaction history includes all transaction types"""
        # Grant subscription credits
        await CreditService.grant_subscription_credits(org_free.id, db_session)

        # Consume credits
        await CreditService.validate_and_consume_credits(
            organization_id=org_free.id,
            amount=3,
            user_id=None,
            reason="Consumption",
            db=db_session
        )

        # Grant manual credits
        await CreditService.grant_manual_credits(
            organization_id=org_free.id,
            amount=5,
            granted_by=super_admin_user.id,
            reason="Manual grant",
            db=db_session
        )

        # Refund credits
        await CreditService.refund_credits(
            organization_id=org_free.id,
            amount=2,
            reason="Refund",
            db=db_session
        )

        transaction_repo = CreditTransactionRepository(db_session)
        transactions = await transaction_repo.get_by_organization_id(org_free.id)

        # Should have 4 transactions total
        assert len(transactions) == 4

        # Check transaction types
        txn_types = {t.transaction_type for t in transactions}
        assert CreditService.TRANSACTION_TYPE_SUBSCRIPTION_GRANT in txn_types
        assert CreditService.TRANSACTION_TYPE_CONSUMPTION in txn_types
        assert CreditService.TRANSACTION_TYPE_MANUAL_ADJUSTMENT in txn_types
        assert CreditService.TRANSACTION_TYPE_REFUND in txn_types

        # Check amounts
        amounts = {t.amount for t in transactions}
        assert 10 in amounts  # Subscription grant
        assert -3 in amounts  # Consumption (negative)
        assert 5 in amounts   # Manual grant
        assert 2 in amounts   # Refund
