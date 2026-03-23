"""
Repository for BillingRequest model.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing_request import BillingRequest
from app.repositories.base import BaseRepository


class BillingRequestRepository(BaseRepository[BillingRequest]):
    """
    Repository for billing request operations.
    """

    def __init__(self, db: AsyncSession, tenant_id: Optional[int] = None):
        super().__init__(db, BillingRequest, tenant_id=tenant_id)

    async def create_request(
        self,
        organization_id: int,
        requested_by_user_id: int,
        request_type: str,
        target_plan: Optional[str],
        target_interval: Optional[str],
        notes: Optional[str],
        status: str = "pending",
        auto_commit: bool = True,
    ) -> BillingRequest:
        billing_request = BillingRequest(
            organization_id=organization_id,
            requested_by_user_id=requested_by_user_id,
            request_type=request_type,
            target_plan=target_plan,
            target_interval=target_interval,
            notes=notes,
            status=status,
        )
        self.db.add(billing_request)
        if auto_commit:
            await self.db.commit()
            await self.db.refresh(billing_request)
        return billing_request

    async def get_latest_pending_by_org(self, organization_id: int) -> Optional[BillingRequest]:
        query = (
            select(BillingRequest)
            .where(
                BillingRequest.organization_id == organization_id,
                BillingRequest.status == "pending",
            )
            .order_by(BillingRequest.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
