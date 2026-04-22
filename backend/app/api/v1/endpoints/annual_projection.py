"""
Annual Sales Projection endpoints (Sprint 20)
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.permission_middleware import require_view_financial_projections
from app.core.tenant import TenantContext, get_tenant_context
from app.models.annual_sales_projection import AnnualSalesProjection
from app.models.service import Service
from app.models.user import User
from app.repositories.annual_sales_projection_repository import AnnualSalesProjectionRepository
from app.schemas.annual_sales_projection import (
    AnnualSalesProjectionCreate,
    AnnualSalesProjectionEntryResponse,
    AnnualSalesProjectionResponse,
    BulkUpdateEntriesRequest,
    MonthlySummary,
    ReplicateMonthRequest,
)
from app.services.annual_sales_projection_service import calculate_projection_summary

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/annual", response_model=AnnualSalesProjectionResponse, summary="Get active annual projection"
)
async def get_active_annual_projection(
    year: int | None = None,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_financial_projections),
    db: AsyncSession = Depends(get_db),
):
    """
    Get active annual projection for current year (or specified year)

    **Permissions:**
    - Requires `can_view_financial_projections` permission (owner, admin_financiero)

    **Query Parameters:**
    - `year`: Optional year (defaults to current year)

    **Returns:**
    - `200 OK`: Projection found
    - `404 Not Found`: No projection found for the year
    """
    if year is None:
        year = datetime.now().year

    repo = AnnualSalesProjectionRepository(db, tenant.organization_id)
    projection = await repo.get_active_projection(tenant.organization_id, year)

    if not projection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active projection found for year {year}",
        )

    # Calculate summary
    summary_data = await calculate_projection_summary(projection, db)

    # Build response
    entries_response = []
    for entry in projection.entries:
        service_name = entry.service.name if entry.service else "Unknown"
        entries_response.append(
            AnnualSalesProjectionEntryResponse(
                id=entry.id,
                service_id=entry.service_id,
                service_name=service_name,
                month=entry.month,
                quantity=entry.quantity,
                hours_per_unit=entry.hours_per_unit,
            )
        )

    monthly_summaries = [MonthlySummary(**s) for s in summary_data["summary"]]

    return AnnualSalesProjectionResponse(
        id=projection.id,
        organization_id=projection.organization_id,
        year=projection.year,
        is_active=projection.is_active,
        notes=projection.notes,
        entries=entries_response,
        summary=monthly_summaries,
        total_annual_revenue=summary_data["total_annual_revenue"],
        total_annual_hours=summary_data["total_annual_hours"],
        break_even_monthly_cost=summary_data["break_even_monthly_cost"],
        created_at=projection.created_at,
        updated_at=projection.updated_at,
        created_by_id=projection.created_by_id,
    )


@router.get(
    "/annual/{year}",
    response_model=AnnualSalesProjectionResponse,
    summary="Get annual projection by year",
)
async def get_annual_projection_by_year(
    year: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_financial_projections),
    db: AsyncSession = Depends(get_db),
):
    """
    Get annual projection for a specific year

    **Permissions:**
    - Requires `can_view_financial_projections` permission
    """
    repo = AnnualSalesProjectionRepository(db, tenant.organization_id)
    projection = await repo.get_by_organization_and_year(tenant.organization_id, year)

    if not projection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"No projection found for year {year}"
        )

    # Calculate summary
    summary_data = await calculate_projection_summary(projection, db)

    # Build response (same as above)
    entries_response = []
    for entry in projection.entries:
        service_name = entry.service.name if entry.service else "Unknown"
        entries_response.append(
            AnnualSalesProjectionEntryResponse(
                id=entry.id,
                service_id=entry.service_id,
                service_name=service_name,
                month=entry.month,
                quantity=entry.quantity,
                hours_per_unit=entry.hours_per_unit,
            )
        )

    monthly_summaries = [MonthlySummary(**s) for s in summary_data["summary"]]

    return AnnualSalesProjectionResponse(
        id=projection.id,
        organization_id=projection.organization_id,
        year=projection.year,
        is_active=projection.is_active,
        notes=projection.notes,
        entries=entries_response,
        summary=monthly_summaries,
        total_annual_revenue=summary_data["total_annual_revenue"],
        total_annual_hours=summary_data["total_annual_hours"],
        break_even_monthly_cost=summary_data["break_even_monthly_cost"],
        created_at=projection.created_at,
        updated_at=projection.updated_at,
        created_by_id=projection.created_by_id,
    )


@router.post(
    "/annual",
    response_model=AnnualSalesProjectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create annual projection",
)
async def create_annual_projection(
    projection_data: AnnualSalesProjectionCreate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_financial_projections),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new annual sales projection

    **Permissions:**
    - Requires `can_view_financial_projections` permission

    **Request Body:**
    - `year`: Year of projection (2020-2100)
    - `notes`: Optional notes
    - `entries`: List of projection entries (service/month combinations)

    **Returns:**
    - `201 Created`: Projection created successfully
    - `400 Bad Request`: Invalid data or projection already exists
    """
    repo = AnnualSalesProjectionRepository(db, tenant.organization_id)

    # Check if projection already exists for this year
    existing = await repo.get_by_organization_and_year(tenant.organization_id, projection_data.year)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Projection for year {projection_data.year} already exists",
        )

    # Validate all services exist and belong to organization
    service_ids = {entry.service_id for entry in projection_data.entries}
    if service_ids:
        services_result = await db.execute(
            select(Service).where(
                Service.id.in_(service_ids),
                Service.organization_id == tenant.organization_id,
                Service.deleted_at.is_(None),
            )
        )
        found_services = {s.id for s in services_result.scalars().all()}
        missing = service_ids - found_services
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Services with IDs {list(missing)} not found or not accessible",
            )

    # Create projection
    projection = AnnualSalesProjection(
        organization_id=tenant.organization_id,
        year=projection_data.year,
        is_active=True,
        notes=projection_data.notes,
        created_by_id=current_user.id,
    )

    projection = await repo.create(projection)

    # Create entries
    if projection_data.entries:
        entries_data = [
            {
                "service_id": entry.service_id,
                "month": entry.month,
                "quantity": entry.quantity,
                "hours_per_unit": entry.hours_per_unit,
            }
            for entry in projection_data.entries
        ]
        await repo.bulk_upsert_entries(projection.id, entries_data)

    # Refresh to get entries
    await db.refresh(projection, ["entries"])

    # Calculate summary
    summary_data = await calculate_projection_summary(projection, db)

    # Build response
    entries_response = []
    for entry in projection.entries:
        service_name = entry.service.name if entry.service else "Unknown"
        entries_response.append(
            AnnualSalesProjectionEntryResponse(
                id=entry.id,
                service_id=entry.service_id,
                service_name=service_name,
                month=entry.month,
                quantity=entry.quantity,
                hours_per_unit=entry.hours_per_unit,
            )
        )

    monthly_summaries = [MonthlySummary(**s) for s in summary_data["summary"]]

    logger.info(
        f"Annual projection created for organization {tenant.organization_id}, year {projection_data.year}",
        user_id=current_user.id,
    )

    return AnnualSalesProjectionResponse(
        id=projection.id,
        organization_id=projection.organization_id,
        year=projection.year,
        is_active=projection.is_active,
        notes=projection.notes,
        entries=entries_response,
        summary=monthly_summaries,
        total_annual_revenue=summary_data["total_annual_revenue"],
        total_annual_hours=summary_data["total_annual_hours"],
        break_even_monthly_cost=summary_data["break_even_monthly_cost"],
        created_at=projection.created_at,
        updated_at=projection.updated_at,
        created_by_id=projection.created_by_id,
    )


@router.put(
    "/annual/{projection_id}",
    response_model=AnnualSalesProjectionResponse,
    summary="Update annual projection",
)
async def update_annual_projection(
    projection_id: int,
    projection_data: AnnualSalesProjectionCreate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_financial_projections),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing annual projection

    **Permissions:**
    - Requires `can_view_financial_projections` permission
    """
    repo = AnnualSalesProjectionRepository(db, tenant.organization_id)
    projection = await repo.get_by_id(projection_id)

    if not projection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Projection {projection_id} not found"
        )

    # Update projection fields
    projection.notes = projection_data.notes
    projection = await repo.update(projection)

    # Update entries
    if projection_data.entries:
        entries_data = [
            {
                "service_id": entry.service_id,
                "month": entry.month,
                "quantity": entry.quantity,
                "hours_per_unit": entry.hours_per_unit,
            }
            for entry in projection_data.entries
        ]
        await repo.bulk_upsert_entries(projection.id, entries_data)

    # Refresh to get entries
    await db.refresh(projection, ["entries"])

    # Calculate summary
    summary_data = await calculate_projection_summary(projection, db)

    # Build response (same as create)
    entries_response = []
    for entry in projection.entries:
        service_name = entry.service.name if entry.service else "Unknown"
        entries_response.append(
            AnnualSalesProjectionEntryResponse(
                id=entry.id,
                service_id=entry.service_id,
                service_name=service_name,
                month=entry.month,
                quantity=entry.quantity,
                hours_per_unit=entry.hours_per_unit,
            )
        )

    monthly_summaries = [MonthlySummary(**s) for s in summary_data["summary"]]

    return AnnualSalesProjectionResponse(
        id=projection.id,
        organization_id=projection.organization_id,
        year=projection.year,
        is_active=projection.is_active,
        notes=projection.notes,
        entries=entries_response,
        summary=monthly_summaries,
        total_annual_revenue=summary_data["total_annual_revenue"],
        total_annual_hours=summary_data["total_annual_hours"],
        break_even_monthly_cost=summary_data["break_even_monthly_cost"],
        created_at=projection.created_at,
        updated_at=projection.updated_at,
        created_by_id=projection.created_by_id,
    )


@router.delete(
    "/annual/{projection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete annual projection",
)
async def delete_annual_projection(
    projection_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_financial_projections),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an annual projection

    **Permissions:**
    - Requires `can_view_financial_projections` permission
    """
    repo = AnnualSalesProjectionRepository(db, tenant.organization_id)
    projection = await repo.get_by_id(projection_id)

    if not projection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Projection {projection_id} not found"
        )

    await repo.delete(projection, soft=False)

    logger.info(f"Annual projection {projection_id} deleted by user {current_user.id}")

    return None


@router.post("/annual/{projection_id}/entries/bulk", summary="Bulk update projection entries")
async def bulk_update_entries(
    projection_id: int,
    request: BulkUpdateEntriesRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_financial_projections),
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk update multiple projection entries (for matrix editing)

    **Permissions:**
    - Requires `can_view_financial_projections` permission
    """
    repo = AnnualSalesProjectionRepository(db, tenant.organization_id)
    projection = await repo.get_by_id(projection_id)

    if not projection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Projection {projection_id} not found"
        )

    # Validate services
    service_ids = {entry.service_id for entry in request.entries}
    if service_ids:
        services_result = await db.execute(
            select(Service).where(
                Service.id.in_(service_ids),
                Service.organization_id == tenant.organization_id,
                Service.deleted_at.is_(None),
            )
        )
        found_services = {s.id for s in services_result.scalars().all()}
        missing = service_ids - found_services
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Services with IDs {list(missing)} not found or not accessible",
            )

    # Bulk upsert entries
    entries_data = [
        {
            "service_id": entry.service_id,
            "month": entry.month,
            "quantity": entry.quantity,
            "hours_per_unit": entry.hours_per_unit,
        }
        for entry in request.entries
    ]

    await repo.bulk_upsert_entries(projection_id, entries_data)

    # Refresh projection
    await db.refresh(projection, ["entries"])

    # Calculate and return summary
    summary_data = await calculate_projection_summary(projection, db)

    return {"success": True, "entries_updated": len(entries_data), "summary": summary_data}


@router.post("/annual/{projection_id}/replicate-month", summary="Replicate month values")
async def replicate_month(
    projection_id: int,
    request: ReplicateMonthRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_financial_projections),
    db: AsyncSession = Depends(get_db),
):
    """
    Replicate values from one month to other months

    **Permissions:**
    - Requires `can_view_financial_projections` permission
    """
    repo = AnnualSalesProjectionRepository(db, tenant.organization_id)
    projection = await repo.get_by_id(projection_id)

    if not projection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Projection {projection_id} not found"
        )

    # Get source month entries
    source_entries = [entry for entry in projection.entries if entry.month == request.source_month]

    if not source_entries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No entries found for source month {request.source_month}",
        )

    # Determine target months
    target_months = request.target_months or [m for m in range(1, 13) if m != request.source_month]

    # Replicate entries
    entries_to_upsert = []
    for source_entry in source_entries:
        for target_month in target_months:
            entries_to_upsert.append(
                {
                    "service_id": source_entry.service_id,
                    "month": target_month,
                    "quantity": source_entry.quantity,
                    "hours_per_unit": source_entry.hours_per_unit,
                }
            )

    await repo.bulk_upsert_entries(projection_id, entries_to_upsert)

    logger.info(
        f"Month {request.source_month} replicated to months {target_months} for projection {projection_id}"
    )

    return {
        "success": True,
        "source_month": request.source_month,
        "target_months": target_months,
        "entries_replicated": len(entries_to_upsert),
    }
