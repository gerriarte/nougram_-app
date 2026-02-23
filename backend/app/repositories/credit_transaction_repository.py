"""
Repository for CreditTransaction model
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.repositories.base import BaseRepository
from app.models.credit_transaction import CreditTransaction


class CreditTransactionRepository(BaseRepository[CreditTransaction]):
    """
    Repository for CreditTransaction model
    """
    def __init__(self, db: AsyncSession, tenant_id: Optional[int] = None):
        super().__init__(db, CreditTransaction, tenant_id)

    async def get_by_organization_id(
        self,
        organization_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[CreditTransaction]:
        """
        Get all transactions for an organization, ordered by created_at DESC
        """
        query = (
            select(CreditTransaction)
            .where(CreditTransaction.organization_id == organization_id)
            .order_by(desc(CreditTransaction.created_at))
        )
        
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_transaction(
        self,
        organization_id: int,
        transaction_type: str,
        amount: int,
        reason: Optional[str] = None,
        reference_id: Optional[int] = None,
        performed_by: Optional[int] = None,
        auto_commit: bool = True,
    ) -> CreditTransaction:
        """
        Create a new credit transaction
        """
        transaction = CreditTransaction(
            organization_id=organization_id,
            transaction_type=transaction_type,
            amount=amount,
            reason=reason,
            reference_id=reference_id,
            performed_by=performed_by
        )
        self.db.add(transaction)
        if auto_commit:
            await self.db.commit()
            await self.db.refresh(transaction)
        return transaction

    async def count_by_organization_id(self, organization_id: int) -> int:
        """
        Count all transactions for an organization.
        """
        query = select(func.count(CreditTransaction.id)).where(
            CreditTransaction.organization_id == organization_id
        )
        result = await self.db.execute(query)
        return int(result.scalar() or 0)

    async def get_latest_by_type(
        self,
        organization_id: int,
        transaction_type: str,
    ) -> Optional[CreditTransaction]:
        """
        Get latest transaction for an organization and type.
        """
        query = (
            select(CreditTransaction)
            .where(
                CreditTransaction.organization_id == organization_id,
                CreditTransaction.transaction_type == transaction_type,
            )
            .order_by(desc(CreditTransaction.created_at))
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()









