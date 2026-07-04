"""
Maintenance endpoints for system cleanup and administration
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.cost import CostFixed
from app.models.project import Project
from app.models.service import Service
from app.models.tax import Tax
from app.models.user import User

router = APIRouter()


class CleanupResponse(BaseModel):
    """Response model for cleanup operations"""

    services_deleted: int = 0
    costs_deleted: int = 0
    taxes_deleted: int = 0
    projects_deleted: int = 0
    total_deleted: int = 0
    message: str


@router.post("/maintenance/cleanup-trash", response_model=CleanupResponse)
async def cleanup_old_trash(
    days_old: int = Query(30, ge=1, le=365, description="Delete items older than this many days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Permanently delete soft-deleted items that have been in trash for more than specified days.

    This is a maintenance operation that should be run periodically to clean up old deleted items.
    Only items that have been soft-deleted for more than 'days_old' days will be permanently deleted.

    Args:
        days_old: Number of days an item must be in trash before permanent deletion (default: 30)
        current_user: Current authenticated user
        db: Database session

    Returns:
        CleanupResponse with counts of deleted items
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    org_id = current_user.organization_id

    services_deleted = 0
    costs_deleted = 0
    taxes_deleted = 0
    projects_deleted = 0

    try:
        # Delete old services (scoped to the caller's organization)
        result = await db.execute(
            select(Service).where(
                and_(
                    Service.organization_id == org_id,
                    Service.deleted_at.isnot(None),
                    Service.deleted_at <= cutoff_date,
                )
            )
        )
        old_services = result.scalars().all()
        for service in old_services:
            await db.delete(service)
        services_deleted = len(old_services)

        # Delete old fixed costs (scoped to the caller's organization)
        result = await db.execute(
            select(CostFixed).where(
                and_(
                    CostFixed.organization_id == org_id,
                    CostFixed.deleted_at.isnot(None),
                    CostFixed.deleted_at <= cutoff_date,
                )
            )
        )
        old_costs = result.scalars().all()
        for cost in old_costs:
            await db.delete(cost)
        costs_deleted = len(old_costs)

        # Delete old taxes (scoped to the caller's organization)
        result = await db.execute(
            select(Tax).where(
                and_(
                    Tax.organization_id == org_id,
                    Tax.deleted_at.isnot(None),
                    Tax.deleted_at <= cutoff_date,
                )
            )
        )
        old_taxes = result.scalars().all()
        for tax in old_taxes:
            await db.delete(tax)
        taxes_deleted = len(old_taxes)

        # Delete old projects (this will cascade to quotes and quote items)
        result = await db.execute(
            select(Project).where(
                and_(
                    Project.organization_id == org_id,
                    Project.deleted_at.isnot(None),
                    Project.deleted_at <= cutoff_date,
                )
            )
        )
        old_projects = result.scalars().all()
        for project in old_projects:
            await db.delete(project)
        projects_deleted = len(old_projects)

        # Commit all deletions
        await db.commit()

        total_deleted = services_deleted + costs_deleted + taxes_deleted + projects_deleted

        return CleanupResponse(
            services_deleted=services_deleted,
            costs_deleted=costs_deleted,
            taxes_deleted=taxes_deleted,
            projects_deleted=projects_deleted,
            total_deleted=total_deleted,
            message=f"Successfully deleted {total_deleted} item(s) that were in trash for more than {days_old} days",
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during cleanup: {str(e)}",
        )


@router.get("/maintenance/trash-stats")
async def get_trash_stats(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Get statistics about items in trash.

    Returns:
        Dictionary with total counts of deleted items by type
    """
    # Count deleted items scoped to the caller's organization
    org_id = current_user.organization_id

    services_result = await db.execute(
        select(Service).where(
            and_(Service.organization_id == org_id, Service.deleted_at.isnot(None))
        )
    )
    services_count = len(services_result.scalars().all())

    costs_result = await db.execute(
        select(CostFixed).where(
            and_(CostFixed.organization_id == org_id, CostFixed.deleted_at.isnot(None))
        )
    )
    costs_count = len(costs_result.scalars().all())

    taxes_result = await db.execute(
        select(Tax).where(and_(Tax.organization_id == org_id, Tax.deleted_at.isnot(None)))
    )
    taxes_count = len(taxes_result.scalars().all())

    projects_result = await db.execute(
        select(Project).where(
            and_(Project.organization_id == org_id, Project.deleted_at.isnot(None))
        )
    )
    projects_count = len(projects_result.scalars().all())

    return {
        "services": services_count,
        "costs": costs_count,
        "taxes": taxes_count,
        "projects": projects_count,
        "total": services_count + costs_count + taxes_count + projects_count,
    }
