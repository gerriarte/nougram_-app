"""
Repository for CreditAccount model
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repositories.base import BaseRepository
from app.models.credit_account import CreditAccount


class CreditAccountRepository(BaseRepository[CreditAccount]):
    """
    Repository for CreditAccount model
    """
    def __init__(self, db: AsyncSession, tenant_id: Optional[int] = None):
        super().__init__(db, CreditAccount, tenant_id)

    async def get_by_organization_id(self, organization_id: int) -> Optional[CreditAccount]:
        """
        Get credit account by organization ID
        """
        query = select(CreditAccount).where(CreditAccount.organization_id == organization_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_for_organization(
        self,
        organization_id: int,
        credits_per_month: Optional[int] = None,
        auto_commit: bool = True,
    ) -> CreditAccount:
        """
        Create a new credit account for an organization
        """
        account = CreditAccount(
            organization_id=organization_id,
            credits_available=0,
            credits_used_total=0,
            credits_used_this_month=0,
            credits_per_month=credits_per_month,
            manual_credits_bonus=0
        )
        self.db.add(account)
        if auto_commit:
            await self.db.commit()
            await self.db.refresh(account)
        return account








