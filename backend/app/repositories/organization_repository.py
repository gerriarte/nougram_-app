"""
Repository for Organization model
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.organization import Organization
from app.models.user import User
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """Repository for Organization operations"""

    def __init__(self, db: AsyncSession, tenant_id: int | None = None):
        # Organizations are global, but we can filter by tenant_id if needed
        super().__init__(db, Organization, tenant_id=None)  # Organizations don't have tenant_id

    async def get_by_slug(self, slug: str) -> Organization | None:
        """Get organization by slug"""
        query = select(Organization).where(Organization.slug == slug)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_with_user_count(self, org_id: int) -> Organization | None:
        """Get organization with user count"""
        query = (
            select(Organization, func.count(User.id).label("user_count"))
            .outerjoin(User, User.organization_id == Organization.id)
            .where(Organization.id == org_id)
            .group_by(Organization.id)
        )

        result = await self.db.execute(query)
        row = result.first()
        if row:
            org = row[0]
            org.user_count = row[1]  # Add user_count as attribute
            return org
        return None

    async def list_all(
        self, page: int = 1, page_size: int = 20, include_inactive: bool = False
    ) -> tuple[list[Organization], int]:
        """List all organizations with pagination"""
        query = select(Organization)

        if not include_inactive:
            query = query.where(Organization.subscription_status == "active")

        # Get total count
        count_query = select(func.count(Organization.id))
        if not include_inactive:
            count_query = count_query.where(Organization.subscription_status == "active")

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Organization.created_at.desc())
        query = query.limit(page_size).offset(offset)

        result = await self.db.execute(query)
        organizations = result.scalars().all()

        # Load user counts for each organization
        for org in organizations:
            user_count_result = await self.db.execute(
                select(func.count(User.id)).where(User.organization_id == org.id)
            )
            org.user_count = user_count_result.scalar() or 0

        return organizations, total

    async def get_users(self, org_id: int) -> list[User]:
        """Get all users in an organization"""
        query = select(User).where(User.organization_id == org_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_user_count(self, org_id: int) -> int:
        """Get count of users in an organization"""
        query = select(func.count(User.id)).where(User.organization_id == org_id)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_project_count(self, org_id: int) -> int:
        """Get count of projects in an organization"""
        from app.models.project import Project

        query = select(func.count(Project.id)).where(
            Project.organization_id == org_id, Project.deleted_at.is_(None)
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def update_subscription(
        self, org_id: int, plan: str | None = None, status: str | None = None
    ) -> Organization | None:
        """Update organization subscription"""
        org = await self.get_by_id(org_id)
        if not org:
            return None

        if plan is not None:
            org.subscription_plan = plan
        if status is not None:
            org.subscription_status = status

        await self.db.commit()
        await self.db.refresh(org)
        return org

    async def update_settings(self, org_id: int, settings: dict) -> Organization | None:
        """Update organization settings JSON."""
        org = await self.get_by_id(org_id)
        if not org:
            return None

        org.settings = settings
        flag_modified(org, "settings")
        await self.db.commit()
        await self.db.refresh(org)
        return org
