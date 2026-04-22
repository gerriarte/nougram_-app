"""
Repository for Annual Sales Projection models
"""

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.annual_sales_projection import AnnualSalesProjection, AnnualSalesProjectionEntry
from app.repositories.base import BaseRepository


class AnnualSalesProjectionRepository(BaseRepository[AnnualSalesProjection]):
    """
    Repository for Annual Sales Projection operations
    """

    def __init__(self, db: AsyncSession, tenant_id: int | None = None):
        super().__init__(db, AnnualSalesProjection, tenant_id=tenant_id)

    async def get_by_organization_and_year(
        self, organization_id: int, year: int
    ) -> AnnualSalesProjection | None:
        """
        Get projection by organization and year

        Args:
            organization_id: Organization ID
            year: Year of projection

        Returns:
            AnnualSalesProjection instance or None
        """
        query = (
            select(AnnualSalesProjection)
            .options(
                selectinload(AnnualSalesProjection.entries).selectinload(
                    AnnualSalesProjectionEntry.service
                )
            )
            .where(
                and_(
                    AnnualSalesProjection.organization_id == organization_id,
                    AnnualSalesProjection.year == year,
                )
            )
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_projection(
        self, organization_id: int, year: int | None = None
    ) -> AnnualSalesProjection | None:
        """
        Get active projection for organization (optionally for specific year)

        Args:
            organization_id: Organization ID
            year: Optional year filter (defaults to current year)

        Returns:
            Active AnnualSalesProjection instance or None
        """
        from datetime import datetime

        if year is None:
            year = datetime.now().year

        query = (
            select(AnnualSalesProjection)
            .options(
                selectinload(AnnualSalesProjection.entries).selectinload(
                    AnnualSalesProjectionEntry.service
                )
            )
            .where(
                and_(
                    AnnualSalesProjection.organization_id == organization_id,
                    AnnualSalesProjection.year == year,
                    AnnualSalesProjection.is_active,
                )
            )
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_entries(self, projection_id: int) -> list[AnnualSalesProjectionEntry]:
        """
        Get all entries for a projection

        Args:
            projection_id: Projection ID

        Returns:
            List of AnnualSalesProjectionEntry instances
        """
        query = (
            select(AnnualSalesProjectionEntry)
            .options(selectinload(AnnualSalesProjectionEntry.service))
            .where(AnnualSalesProjectionEntry.projection_id == projection_id)
            .order_by(AnnualSalesProjectionEntry.service_id, AnnualSalesProjectionEntry.month)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def upsert_entry(
        self, projection_id: int, service_id: int, month: int, quantity: int, hours_per_unit: float
    ) -> AnnualSalesProjectionEntry:
        """
        Upsert (insert or update) an entry

        Args:
            projection_id: Projection ID
            service_id: Service ID
            month: Month (1-12)
            quantity: Quantity of services
            hours_per_unit: Hours per unit

        Returns:
            AnnualSalesProjectionEntry instance
        """
        # Try to find existing entry
        query = select(AnnualSalesProjectionEntry).where(
            and_(
                AnnualSalesProjectionEntry.projection_id == projection_id,
                AnnualSalesProjectionEntry.service_id == service_id,
                AnnualSalesProjectionEntry.month == month,
            )
        )

        result = await self.db.execute(query)
        entry = result.scalar_one_or_none()

        if entry:
            # Update existing
            entry.quantity = quantity
            entry.hours_per_unit = hours_per_unit
        else:
            # Create new
            entry = AnnualSalesProjectionEntry(
                projection_id=projection_id,
                service_id=service_id,
                month=month,
                quantity=quantity,
                hours_per_unit=hours_per_unit,
            )
            self.db.add(entry)

        await self.db.flush()
        await self.db.refresh(entry)
        return entry

    async def bulk_upsert_entries(
        self, projection_id: int, entries: list[dict]
    ) -> list[AnnualSalesProjectionEntry]:
        """
        Bulk upsert multiple entries

        Args:
            projection_id: Projection ID
            entries: List of entry dicts with keys: service_id, month, quantity, hours_per_unit

        Returns:
            List of AnnualSalesProjectionEntry instances
        """
        result_entries = []

        for entry_data in entries:
            entry = await self.upsert_entry(
                projection_id=projection_id,
                service_id=entry_data["service_id"],
                month=entry_data["month"],
                quantity=entry_data["quantity"],
                hours_per_unit=entry_data["hours_per_unit"],
            )
            result_entries.append(entry)

        await self.db.commit()
        return result_entries

    async def delete_entry(self, entry_id: int) -> None:
        """
        Delete an entry

        Args:
            entry_id: Entry ID
        """
        query = select(AnnualSalesProjectionEntry).where(AnnualSalesProjectionEntry.id == entry_id)

        result = await self.db.execute(query)
        entry = result.scalar_one_or_none()

        if entry:
            await self.db.delete(entry)
            await self.db.flush()
