"""
Repository for financial ledger events (provider-agnostic payment tracking).
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial_ledger import FinancialLedgerEvent
from app.repositories.base import BaseRepository


class FinancialLedgerRepository(BaseRepository[FinancialLedgerEvent]):
    def __init__(self, db: AsyncSession, tenant_id: Optional[int] = None):
        super().__init__(db, FinancialLedgerEvent, tenant_id=tenant_id)

    async def create_event(
        self,
        organization_id: int,
        event_type: str,
        amount: Decimal,
        currency: str = "USD",
        status: str = "completed",
        provider: str = "manual",
        external_id: Optional[str] = None,
        reference: Optional[str] = None,
        metadata_json: Optional[str] = None,
    ) -> FinancialLedgerEvent:
        entity = FinancialLedgerEvent(
            organization_id=organization_id,
            event_type=event_type,
            provider=provider,
            amount=amount,
            currency=currency,
            status=status,
            external_id=external_id,
            reference=reference,
            metadata_json=metadata_json,
        )
        return await self.create(entity)

    async def list_by_organization(
        self,
        organization_id: int,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        provider: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> List[FinancialLedgerEvent]:
        query = select(FinancialLedgerEvent).where(FinancialLedgerEvent.organization_id == organization_id)
        if since is not None:
            query = query.where(FinancialLedgerEvent.created_at >= since)
        if until is not None:
            query = query.where(FinancialLedgerEvent.created_at <= until)
        if provider is not None:
            query = query.where(FinancialLedgerEvent.provider == provider)
        query = query.order_by(desc(FinancialLedgerEvent.created_at)).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())
