"""
Repository for AuditLog model
"""

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """
    Repository for audit log operations
    Note: Audit logs don't use tenant scoping as they may need to be queried across organizations
    """

    def __init__(self, db: AsyncSession):
        super().__init__(db, AuditLog, tenant_id=None)  # No tenant scoping for audit logs

    async def create_log(
        self,
        action: str,
        user_id: int | None = None,
        organization_id: int | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: str | None = None,
        status: str = "success",
        error_message: str | None = None,
    ) -> AuditLog:
        """
        Create a new audit log entry

        Args:
            action: Action name (e.g., "user.login", "project.create")
            user_id: User ID who performed the action
            organization_id: Organization ID (if applicable)
            resource_type: Type of resource affected (e.g., "project", "user")
            resource_id: ID of the affected resource
            ip_address: IP address of the requester
            user_agent: User agent string
            details: Additional details (JSON or text)
            status: Action status (success, failure, error)
            error_message: Error message if status is failure/error

        Returns:
            Created AuditLog instance
        """
        audit_log = AuditLog(
            action=action,
            user_id=user_id,
            organization_id=organization_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            status=status,
            error_message=error_message,
        )

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)

        return audit_log

    async def get_by_organization(
        self,
        organization_id: int,
        limit: int | None = 100,
        offset: int | None = 0,
        action: str | None = None,
        status: str | None = None,
    ) -> list[AuditLog]:
        """
        Get audit logs for a specific organization

        Args:
            organization_id: Organization ID
            limit: Maximum number of results
            offset: Number of results to skip
            action: Filter by action (optional)
            status: Filter by status (optional)

        Returns:
            List of audit logs
        """
        query = select(AuditLog).where(AuditLog.organization_id == organization_id)

        if action:
            query = query.where(AuditLog.action == action)

        if status:
            query = query.where(AuditLog.status == status)

        query = query.order_by(desc(AuditLog.created_at))

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_user(
        self, user_id: int, limit: int | None = 100, offset: int | None = 0
    ) -> list[AuditLog]:
        """
        Get audit logs for a specific user

        Args:
            user_id: User ID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of audit logs
        """
        query = (
            select(AuditLog).where(AuditLog.user_id == user_id).order_by(desc(AuditLog.created_at))
        )

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())
