"""
Project management endpoints
"""

import logging
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

from sqlalchemy import delete as sql_delete
from sqlalchemy import insert
from sqlalchemy import update as sql_update

from app.core.calculations import (
    calculate_blended_cost_rate,
    calculate_quote_totals_enhanced,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError
from app.core.pdf_generator import generate_quote_pdf
from app.core.permission_middleware import require_create_projects
from app.core.permissions import (
    PERM_DELETE_RESOURCES,
    PermissionError,
    check_permission,
    get_user_role,
)
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant_context
from app.models.project import (
    Project,
    Quote,
    QuoteExpense,
    QuoteItem,
    QuoteItemAllocation,
    QuoteItemCellAssignment,
    project_taxes,
)
from app.models.proposal import ProposalClientLink
from app.models.service import Service
from app.models.tax import Tax
from app.models.team import TeamMember
from app.models.team_cells import TeamCellVersion
from app.models.user import User
from app.repositories.factory import RepositoryFactory
from app.schemas.project import (
    ClientSearchResponse,
    ClientSearchResult,
    ProjectCreateWithQuote,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
    QuoteCreateNewVersion,
    QuoteItemAllocationResponse,
    QuoteItemResponse,
    QuoteResponse,
    QuoteResponseWithItems,
    QuoteUpdate,
)
from app.schemas.quote import (
    MarginSummary,
    QuoteEmailRequest,
    QuoteEmailResponse,
    QuoteExpenseResponse,
)
from app.services.capacity_service import CapacityService
from app.services.settings_service import SettingsService

router = APIRouter()


async def _get_cell_version_for_quote(
    db: AsyncSession,
    organization_id: int,
    cell_id: int,
    cell_version_id: int | None,
    cache: dict[tuple[int, int | None], TeamCellVersion],
) -> TeamCellVersion:
    cache_key = (cell_id, cell_version_id)
    if cache_key in cache:
        return cache[cache_key]

    query = (
        select(TeamCellVersion)
        .where(
            TeamCellVersion.organization_id == organization_id,
            TeamCellVersion.cell_id == cell_id,
        )
        .options(selectinload(TeamCellVersion.members))
        .order_by(TeamCellVersion.version_number.desc())
    )
    if cell_version_id is not None:
        query = query.where(TeamCellVersion.id == cell_version_id)
    result = await db.execute(query)
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cell version not found for cell_id={cell_id}",
        )
    cache[cache_key] = version
    return version


async def _expand_cell_assignment_for_quote(
    db: AsyncSession,
    organization_id: int,
    cell_assignment,
    cache: dict[tuple[int, int | None], TeamCellVersion],
) -> tuple[TeamCellVersion, list[dict], Decimal]:
    if not settings.FEATURE_TEAM_CELLS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team cells feature is disabled for this environment.",
        )

    cell_id = int(cell_assignment.cell_id)
    requested_version_id = getattr(cell_assignment, "cell_version_id", None)
    occupancy_pct = Decimal(str(getattr(cell_assignment, "occupancy_percentage", 0)))
    duration_months = int(getattr(cell_assignment, "duration_months", 1) or 1)
    if occupancy_pct <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="occupancy_percentage must be greater than 0",
        )

    version = await _get_cell_version_for_quote(
        db=db,
        organization_id=organization_id,
        cell_id=cell_id,
        cell_version_id=requested_version_id,
        cache=cache,
    )
    active_members = [m for m in (version.members or []) if m.is_active]
    if not active_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cell version {version.id} has no active members.",
        )

    member_ids = [member.team_member_id for member in active_members]
    member_result = await db.execute(
        select(TeamMember).where(
            TeamMember.organization_id == organization_id,
            TeamMember.id.in_(member_ids),
            TeamMember.is_active,
        )
    )
    team_members = {member.id: member for member in member_result.scalars().all()}
    if len(team_members) != len(set(member_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more cell members are invalid or inactive.",
        )

    total_weight = sum(Decimal(str(member.weight or 0)) for member in active_members)
    if total_weight <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cell version weights must be greater than 0.",
        )

    occupancy_ratio = occupancy_pct / Decimal("100")
    allocations: list[dict] = []
    total_hours = Decimal("0")
    for member in active_members:
        tm = team_members[member.team_member_id]
        weekly_hours = Decimal(str(tm.billable_hours_per_week or 0))
        non_billable = Decimal(str(tm.non_billable_hours_percentage or 0))
        capacity_monthly = weekly_hours * Decimal("4.33") * (Decimal("1") - non_billable)
        normalized_weight = Decimal(str(member.weight or 0)) / total_weight
        hours = (
            capacity_monthly * occupancy_ratio * Decimal(str(duration_months)) * normalized_weight
        )
        if hours <= 0:
            continue
        total_hours += hours
        allocations.append(
            {
                "team_member_id": member.team_member_id,
                "hours": hours,
                "role": member.role_override,
                "start_date": None,
                "end_date": None,
            }
        )

    if total_hours <= 0 or not allocations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cell assignment expansion produced zero hours.",
        )

    return version, allocations, total_hours


def _compute_quote_tax_totals(quote: Quote, project: Project) -> tuple[Decimal, Decimal]:
    """Compute total_taxes and total_with_taxes from quote + project taxes."""
    total_client_price = (
        quote.total_client_price if quote.total_client_price is not None else Decimal("0")
    )
    total_taxes = Decimal("0")

    for tax in project.taxes or []:
        percentage = tax.percentage if tax.percentage is not None else Decimal("0")
        total_taxes += (total_client_price * percentage) / Decimal("100")

    total_with_taxes = total_client_price + total_taxes
    return total_taxes, total_with_taxes


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= 0:
        return Decimal("0")
    return numerator / denominator


def _quote_is_active(quote: Quote) -> bool:
    return bool(getattr(quote, "is_active", 1))


def _build_margin_summary(
    total_client_price: Decimal | None,
    total_internal_cost: Decimal | None,
    total_taxes: Decimal | None,
    gross_margin_ratio: Decimal | None,
    target_margin_ratio: Decimal | None,
) -> MarginSummary:
    client = total_client_price if total_client_price is not None else Decimal("0")
    internal = total_internal_cost if total_internal_cost is not None else Decimal("0")
    taxes = total_taxes if total_taxes is not None else Decimal("0")
    gross = gross_margin_ratio if gross_margin_ratio is not None else Decimal("0")
    net = _safe_ratio(client - internal - taxes, client)
    tax_burden = _safe_ratio(taxes, client)
    return MarginSummary(
        gross_margin_ratio=gross,
        net_margin_ratio=net,
        target_margin_ratio=target_margin_ratio,
        tax_burden_ratio=tax_burden,
    )


def _apply_contingency_to_totals(
    totals: dict,
    contingency_type: str | None,
    contingency_value: Decimal | None,
) -> dict:
    if not contingency_type or contingency_value is None:
        return totals
    try:
        contingency_numeric = Decimal(str(contingency_value))
    except Exception:
        contingency_numeric = Decimal("0")
    if contingency_numeric <= 0:
        return totals

    base_price = Decimal(str(totals.get("total_client_price", 0) or 0))
    internal_cost = Decimal(str(totals.get("total_internal_cost", 0) or 0))

    if contingency_type == "fixed":
        extra = contingency_numeric
    else:
        extra = base_price * (contingency_numeric / Decimal("100"))

    total_with_contingency = base_price + extra
    totals["total_client_price"] = float(total_with_contingency)
    if total_with_contingency > 0:
        totals["margin_percentage"] = float(
            (total_with_contingency - internal_cost) / total_with_contingency
        )
    return totals


def _proposal_to_notes_text(proposal_body: dict | None) -> str:
    if not proposal_body:
        return ""
    parts: list[str] = []
    summary = proposal_body.get("executive_summary")
    if isinstance(summary, str) and summary.strip():
        parts.append(summary.strip())

    description = proposal_body.get("description")
    if isinstance(description, str) and description.strip():
        parts.append(f"\nDescripcion del proyecto:\n{description.strip()}")

    objectives = proposal_body.get("objectives")
    if isinstance(objectives, list) and objectives:
        objective_lines = [f"- {obj}" for obj in objectives if isinstance(obj, str) and obj.strip()]
        if objective_lines:
            parts.append("\nObjetivos:\n" + "\n".join(objective_lines))

    deliverables = proposal_body.get("deliverables")
    if isinstance(deliverables, list) and deliverables:
        deliverable_lines = []
        for item in deliverables:
            if isinstance(item, dict):
                name = str(item.get("name") or "").strip()
                status = str(item.get("status") or "").strip()
                if name:
                    deliverable_lines.append(f"- {name}" + (f" ({status})" if status else ""))
            elif isinstance(item, str) and item.strip():
                deliverable_lines.append(f"- {item.strip()}")
        if deliverable_lines:
            parts.append("\nEntregables:\n" + "\n".join(deliverable_lines))

    scope = proposal_body.get("scope")
    if isinstance(scope, str) and scope.strip():
        parts.append(f"\nAlcance:\n{scope.strip()}")

    timeline = proposal_body.get("timeline")
    if isinstance(timeline, str) and timeline.strip():
        parts.append(f"\nCronograma / hitos:\n{timeline.strip()}")

    conditions = proposal_body.get("conditions")
    if isinstance(conditions, str) and conditions.strip():
        parts.append(f"\nCondiciones:\n{conditions.strip()}")

    free_text = proposal_body.get("free_text")
    if isinstance(free_text, str) and free_text.strip():
        parts.append(free_text.strip())

    return "\n".join(parts).strip()


@router.get("/", response_model=ProjectListResponse, summary="List all projects")
async def list_projects(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status_filter: str = None,
    include_deleted: bool = False,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
):
    """
    List all projects with pagination
    Optionally filter by status (Draft, Sent, Won, Lost)
    By default, excludes soft-deleted items (deleted_at IS NULL)
    """
    # #region agent log
    try:
        import json
        import time
        from pathlib import Path

        log_data = {
            "sessionId": "debug-session",
            "runId": "test-list-projects",
            "hypothesisId": "A",
            "location": "projects.py:61",
            "message": "list_projects called",
            "data": {"tenant_org_id": tenant.organization_id, "user_id": current_user.id},
            "timestamp": int(time.time() * 1000),
        }
        log_file = Path(r"c:\Users\Usuario\Documents\GitHub\Cotizador\.cursor\debug.log")
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_data) + "\n")
    except Exception:
        pass
    # #endregion

    from sqlalchemy import desc

    # Use RepositoryFactory to get project repository with tenant scoping
    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)

    # Calculate pagination offset
    offset = (page - 1) * page_size

    # Build where clause for status filter
    where_clause = None
    if status_filter:
        where_clause = Project.status == status_filter

    # Get paginated projects with taxes loaded
    projects = await project_repo.get_all_paginated(
        include_deleted=include_deleted,
        status_filter=status_filter,
        order_by=desc(Project.created_at),
        limit=page_size,
        offset=offset,
    )

    # Get total count
    total = await project_repo.count(where=where_clause, include_deleted=include_deleted)

    # Build response with taxes
    items = []
    for project in projects:
        project_dict = {
            "id": project.id,
            "name": project.name,
            "client_id": getattr(project, "client_id", None),
            "client_name": project.client_name,
            "client_email": project.client_email,
            "status": project.status,
            "currency": project.currency,
            "tax_ids": [tax.id for tax in project.taxes],
            "taxes": [
                {"id": tax.id, "name": tax.name, "code": tax.code, "percentage": tax.percentage}
                for tax in project.taxes
            ],
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }
        items.append(ProjectResponse.model_validate(project_dict))

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return ProjectListResponse(
        items=items, total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@router.get(
    "/clients/search", response_model=ClientSearchResponse, summary="Search existing clients"
)
async def search_clients(
    q: str = Query(..., min_length=2, description="Search query (client name or email)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Search existing clients by name or email

    This endpoint provides autocomplete functionality for client selection
    in the quote creation flow. It searches across all projects in the organization
    and returns unique clients matching the search query.

    **Permissions:**
    - All authenticated users can search clients for their organization

    **Query Parameters:**
    - `q`: Search query (minimum 2 characters) - searches in client name and email
    - `limit`: Maximum number of results (1-50, default: 10)

    **Returns:**
    - `200 OK`: List of matching clients
    - `400 Bad Request`: Search query too short
    - `500 Internal Server Error`: Error searching clients

    **Response includes:**
    - `clients`: List of matching clients with:
      - `name`: Client name
      - `email`: Client email (if available)
      - `project_count`: Number of projects with this client
      - `last_project_date`: Date of the most recent project
    - `total`: Total number of clients found

    **Example:**
    ```
    GET /api/v1/projects/clients/search?q=Tech&limit=5
    ```
    """
    from app.services.project_service import ProjectService

    if len(q.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query must be at least 2 characters long",
        )
    limit = min(max(limit, 1), 50)
    project_service = ProjectService(db, tenant.organization_id)
    clients_data = await project_service.search_clients(search_query=q, limit=limit)
    clients = [
        ClientSearchResult(
            name=client["name"],
            email=client["email"],
            project_count=client["project_count"],
            last_project_date=client["last_project_date"],
        )
        for client in clients_data
    ]
    return ClientSearchResponse(clients=clients, total=len(clients))


@router.post(
    "/",
    response_model=QuoteResponseWithItems,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project with initial quote",
)
async def create_project(
    project_data: ProjectCreateWithQuote,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_create_projects),  # Require permission to create projects
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new project with initial quote

    **Permissions:**
    - Requires `can_create_projects` permission
    - Allowed roles: owner, admin_financiero, product_manager, super_admin
    - Note: Creating a quote consumes 1 credit for the organization
    """

    from app.services.project_service import ProjectService

    try:
        project_service = ProjectService(db, tenant.organization_id)
        result = await project_service.create_project_with_quote(
            project_data=project_data,
            current_user=current_user,
            subscription_plan=tenant.subscription_plan,
        )
        return result
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating project: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}",
        )


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get project by ID")
async def get_project(
    project_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    include_deleted: bool = False,
):
    """
    Get a specific project by ID (with tenant scoping)
    By default, excludes soft-deleted items
    """
    # Use RepositoryFactory to get project repository with tenant scoping
    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)

    # Get project - repository automatically filters by tenant and validates ownership
    project = await project_repo.get_by_id_with_quotes(project_id, include_deleted=include_deleted)

    if not project:
        raise ResourceNotFoundError("Project", project_id)

    # Build response with taxes
    project_dict = {
        "id": project.id,
        "name": project.name,
        "client_id": getattr(project, "client_id", None),
        "client_name": project.client_name,
        "client_email": project.client_email,
        "status": project.status,
        "currency": project.currency,
        "tax_ids": [tax.id for tax in project.taxes],
        "taxes": [
            {"id": tax.id, "name": tax.name, "code": tax.code, "percentage": tax.percentage}
            for tax in project.taxes
        ],
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }

    return ProjectResponse.model_validate(project_dict)


@router.put("/{project_id}", response_model=ProjectResponse, summary="Update project")
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing project (with tenant scoping)
    Cannot update soft-deleted projects
    Validates ownership automatically via repository tenant scoping
    """
    # Use RepositoryFactory to get project repository with tenant scoping
    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)

    # Get project - repository automatically filters by tenant (validates ownership)
    project = await project_repo.get_by_id_with_quotes(project_id, include_deleted=False)

    if not project:
        raise ResourceNotFoundError("Project", project_id)

    update_data = project_data.model_dump(exclude_unset=True)
    settings_service = SettingsService(db)
    primary_currency = await settings_service.get_primary_currency(tenant.organization_id)

    # Handle tax_ids separately
    tax_ids = update_data.pop("tax_ids", None)
    if "currency" in update_data:
        incoming_currency = update_data.get("currency")
        if incoming_currency and incoming_currency != primary_currency:
            logger.warning(
                "Overriding project currency update with organization primary currency "
                f"(project_id={project_id}, organization_id={tenant.organization_id}, "
                f"incoming_currency={incoming_currency}, primary_currency={primary_currency})"
            )
        update_data["currency"] = primary_currency

    for field, value in update_data.items():
        setattr(project, field, value)

    # Update taxes if provided
    if tax_ids is not None:
        result = await db.execute(
            select(Tax).where(
                Tax.id.in_(tax_ids),
                Tax.organization_id == tenant.organization_id,
                Tax.is_active,
                Tax.deleted_at.is_(None),
            )
        )
        taxes = result.scalars().all()
        if len(taxes) != len(tax_ids):
            missing = set(tax_ids) - {tax.id for tax in taxes}
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Taxes with ids {list(missing)} not found, inactive, or deleted",
            )
        # Remove existing tax associations
        await db.execute(sql_delete(project_taxes).where(project_taxes.c.project_id == project_id))
        # Add new tax associations using association table directly
        if taxes:
            await db.execute(
                insert(project_taxes).values(
                    [{"project_id": project_id, "tax_id": tax.id} for tax in taxes]
                )
            )

    await db.commit()

    # Reload project with taxes relationship loaded to avoid lazy loading issues
    project = await project_repo.get_by_id_with_quotes(project_id, include_deleted=False)

    # Build response with taxes (now properly loaded)
    project_dict = {
        "id": project.id,
        "name": project.name,
        "client_id": getattr(project, "client_id", None),
        "client_name": project.client_name,
        "client_email": project.client_email,
        "status": project.status,
        "currency": project.currency,
        "tax_ids": [tax.id for tax in project.taxes],
        "taxes": [
            {"id": tax.id, "name": tax.name, "code": tax.code, "percentage": tax.percentage}
            for tax in project.taxes
        ],
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }

    return ProjectResponse.model_validate(project_dict)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete a project (move to trash)
    Projects are not permanently deleted, allowing restoration

    **Permissions:**
    - Requires `can_delete_resources` permission
    """
    try:
        check_permission(current_user, PERM_DELETE_RESOURCES)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete projects",
        )
    # #region agent log
    try:
        import json
        import time
        from pathlib import Path

        log_data = {
            "sessionId": "debug-session",
            "runId": "test-delete-project",
            "hypothesisId": "B",
            "location": "projects.py:454",
            "message": "delete_project called",
            "data": {
                "project_id": project_id,
                "tenant_org_id": tenant.organization_id,
                "user_id": current_user.id,
            },
            "timestamp": int(time.time() * 1000),
        }
        log_file = Path(r"c:\Users\Usuario\Documents\GitHub\Cotizador\.cursor\debug.log")
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_data) + "\n")
    except Exception:
        pass
    # #endregion

    # Use RepositoryFactory to get project repository with tenant scoping
    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)

    # Get project - repository automatically validates ownership via tenant scoping
    project = await project_repo.get_by_id(project_id, include_deleted=False)

    if not project:
        raise ResourceNotFoundError("Project", project_id)

    # Soft delete using repository method (validates ownership automatically)
    await project_repo.delete(project, soft=True, deleted_by_id=current_user.id)

    return None


@router.post("/{project_id}/restore", response_model=ProjectResponse)
async def restore_project(
    project_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Restore a soft-deleted project from trash
    """
    # Use RepositoryFactory to get project repository with tenant scoping
    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)

    # Get project (including deleted) - repository automatically validates ownership via tenant scoping
    project = await project_repo.get_by_id_with_quotes(project_id, include_deleted=True)

    if not project or project.deleted_at is None:
        raise ResourceNotFoundError("Project", project_id)

    # Restore: clear deleted fields
    project.deleted_at = None
    project.deleted_by_id = None
    await db.commit()
    await db.refresh(project)

    # Build response
    project_dict = {
        "id": project.id,
        "name": project.name,
        "client_id": getattr(project, "client_id", None),
        "client_name": project.client_name,
        "client_email": project.client_email,
        "status": project.status,
        "currency": project.currency,
        "tax_ids": [tax.id for tax in project.taxes],
        "taxes": [
            {"id": tax.id, "name": tax.name, "code": tax.code, "percentage": tax.percentage}
            for tax in project.taxes
        ],
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }

    return ProjectResponse.model_validate(project_dict)


@router.get("/trash/list", response_model=ProjectListResponse)
async def list_deleted_projects(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all soft-deleted projects (trash)
    """
    from sqlalchemy import desc

    # Use RepositoryFactory to get project repository with tenant scoping
    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)

    # Get all deleted projects - repository automatically filters by tenant
    projects = await project_repo.get_all_paginated(
        include_deleted=True,
        only_deleted=True,
        order_by=desc(Project.deleted_at),
        limit=None,
        offset=None,
    )

    # Build response with taxes and user info
    items = []
    for project in projects:
        project_dict = {
            "id": project.id,
            "name": project.name,
            "client_id": getattr(project, "client_id", None),
            "client_name": project.client_name,
            "client_email": project.client_email,
            "status": project.status,
            "currency": project.currency,
            "tax_ids": [tax.id for tax in project.taxes],
            "taxes": [
                {"id": tax.id, "name": tax.name, "code": tax.code, "percentage": tax.percentage}
                for tax in project.taxes
            ],
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "deleted_at": project.deleted_at,
            "deleted_by_id": project.deleted_by_id,
            "deleted_by_name": project.deleted_by.name if project.deleted_by else None,
            "deleted_by_email": project.deleted_by.email if project.deleted_by else None,
        }
        items.append(ProjectResponse.model_validate(project_dict))

    return ProjectListResponse(items=items, total=len(projects))


@router.delete("/{project_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def permanently_delete_project(
    project_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Permanently delete a soft-deleted project (hard delete)
    This action cannot be undone. Only soft-deleted projects can be permanently deleted.
    This will cascade delete all quotes and quote items associated with the project.
    Validates ownership automatically via repository tenant scoping

    **Permissions:**
    - Requires `can_delete_resources` permission
    """
    try:
        check_permission(current_user, PERM_DELETE_RESOURCES)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to permanently delete projects",
        )
    # Use RepositoryFactory to get project repository with tenant scoping
    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)

    # Get project (including deleted) - repository automatically validates ownership via tenant scoping
    project = await project_repo.get_by_id_with_quotes(project_id, include_deleted=True)

    if not project or project.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found in trash. Only soft-deleted projects can be permanently deleted.",
        )

    # Hard delete using repository method (validates ownership automatically)
    await project_repo.delete(project, soft=False)

    return None


@router.get("/{project_id}/quotes/{quote_id}", response_model=QuoteResponseWithItems)
async def get_quote(
    project_id: int,
    quote_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific quote with all items
    Validates ownership via repository tenant scoping
    """
    # Use RepositoryFactory to get project repository with tenant scoping
    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)

    # Verify project exists and belongs to tenant (load taxes eagerly for totals computation)
    project = await project_repo.get_by_id_with_quotes(project_id, include_deleted=False)
    if not project:
        raise ResourceNotFoundError("Project", project_id)

    # Get quote using repository method (validates ownership via project's tenant)
    quote = await project_repo.get_quote_by_id(quote_id)

    if not quote or quote.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote with id {quote_id} for project {project_id} not found",
        )
    if not _quote_is_active(quote):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote with id {quote_id} for project {project_id} is inactive",
        )

    # Build items response with service names
    items_response = []
    for item in quote.items:
        items_response.append(
            QuoteItemResponse(
                id=item.id,
                service_id=item.service_id,
                service_name=item.custom_service_name
                or (item.service.name if item.service else None),
                custom_service_name=item.custom_service_name,
                estimated_hours=item.estimated_hours,
                pricing_type=getattr(item, "pricing_type", None),
                fixed_price=getattr(item, "fixed_price", None),
                quantity=getattr(item, "quantity", None),
                recurring_price=getattr(item, "recurring_price", None),
                billing_frequency=getattr(item, "billing_frequency", None),
                project_value=getattr(item, "project_value", None),
                cell_assignment=(
                    {
                        "id": item.cell_assignment.id,
                        "cell_id": item.cell_assignment.cell_id,
                        "cell_version_id": item.cell_assignment.cell_version_id,
                        "occupancy_percentage": item.cell_assignment.occupancy_percentage,
                        "duration_months": item.cell_assignment.duration_months,
                    }
                    if getattr(item, "cell_assignment", None) is not None
                    else None
                ),
                internal_cost=item.internal_cost,
                client_price=item.client_price,
                margin_percentage=item.margin_percentage,
                allocations=[
                    QuoteItemAllocationResponse(
                        id=alloc.id,
                        team_member_id=alloc.team_member_id,
                        hours=alloc.hours,
                        role=alloc.role,
                        start_date=alloc.start_date,
                        end_date=alloc.end_date,
                    )
                    for alloc in (item.allocations or [])
                ],
            )
        )

    total_taxes, total_with_taxes = _compute_quote_tax_totals(quote, project)

    expenses_response = [
        QuoteExpenseResponse(
            id=exp.id,
            quote_id=exp.quote_id,
            name=exp.name,
            description=exp.description,
            cost=exp.cost,
            markup_percentage=exp.markup_percentage,
            client_price=exp.client_price,
            category=exp.category,
            quantity=exp.quantity,
        )
        for exp in (quote.expenses or [])
    ]

    return QuoteResponseWithItems(
        id=quote.id,
        project_id=quote.project_id,
        version=quote.version,
        total_internal_cost=quote.total_internal_cost,
        total_client_price=quote.total_client_price,
        total_taxes=total_taxes,
        total_with_taxes=total_with_taxes,
        margin_percentage=quote.margin_percentage,
        margin=_build_margin_summary(
            total_client_price=quote.total_client_price,
            total_internal_cost=quote.total_internal_cost,
            total_taxes=total_taxes,
            gross_margin_ratio=quote.margin_percentage,
            target_margin_ratio=quote.target_margin_percentage,
        ),
        contingency_description=getattr(quote, "contingency_description", None),
        contingency_type=getattr(quote, "contingency_type", None),
        contingency_value=getattr(quote, "contingency_value", None),
        notes=quote.notes,
        is_active=bool(getattr(quote, "is_active", 1)),
        deletion_requested_at=getattr(quote, "deletion_requested_at", None),
        deletion_requested_by_id=getattr(quote, "deletion_requested_by_id", None),
        deletion_request_reason=getattr(quote, "deletion_request_reason", None),
        created_at=quote.created_at,
        updated_at=quote.updated_at,
        items=items_response,
        expenses=expenses_response,
    )


@router.get("/{project_id}/quotes", response_model=list[QuoteResponse])
async def list_project_quotes(
    project_id: int,
    include_inactive: bool = Query(False, description="Include inactive quotes for audit views"),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all quotes for a project (with tenant scoping)
    Validates ownership via repository tenant scoping
    """
    # Use RepositoryFactory to get project repository with tenant scoping
    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)

    # Verify project exists and belongs to tenant (validates ownership)
    project = await project_repo.get_by_id_with_quotes(project_id, include_deleted=False)
    if not project:
        raise ResourceNotFoundError("Project", project_id)

    quotes_source = project.quotes or []
    if not include_inactive:
        quotes_source = [q for q in quotes_source if _quote_is_active(q)]
    quotes = sorted(quotes_source, key=lambda q: q.version, reverse=True)

    response_quotes: list[QuoteResponse] = []
    for quote in quotes:
        total_taxes, total_with_taxes = _compute_quote_tax_totals(quote, project)
        response_quotes.append(
            QuoteResponse(
                id=quote.id,
                project_id=quote.project_id,
                version=quote.version,
                total_internal_cost=quote.total_internal_cost,
                total_client_price=quote.total_client_price,
                total_taxes=total_taxes,
                total_with_taxes=total_with_taxes,
                margin_percentage=quote.margin_percentage,
                target_margin_percentage=quote.target_margin_percentage,
                margin=_build_margin_summary(
                    total_client_price=quote.total_client_price,
                    total_internal_cost=quote.total_internal_cost,
                    total_taxes=total_taxes,
                    gross_margin_ratio=quote.margin_percentage,
                    target_margin_ratio=quote.target_margin_percentage,
                ),
                contingency_description=getattr(quote, "contingency_description", None),
                contingency_type=getattr(quote, "contingency_type", None),
                contingency_value=getattr(quote, "contingency_value", None),
                notes=quote.notes,
                is_active=bool(getattr(quote, "is_active", 1)),
                deletion_requested_at=getattr(quote, "deletion_requested_at", None),
                deletion_requested_by_id=getattr(quote, "deletion_requested_by_id", None),
                deletion_request_reason=getattr(quote, "deletion_request_reason", None),
                revisions_included=getattr(quote, "revisions_included", 2),
                revision_cost_per_additional=getattr(quote, "revision_cost_per_additional", None),
                created_at=quote.created_at,
                updated_at=quote.updated_at,
            )
        )

    return response_quotes


@router.delete("/{project_id}/quotes/{quote_id}")
async def delete_or_request_quote_deletion(
    project_id: int,
    quote_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete quote by role policy:
    - super_admin / owner / admin_financiero: hard delete
    - product_manager: request deletion (deactivate quote)
    """
    try:
        project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)

        project = await project_repo.get_by_id_with_quotes(project_id, include_deleted=False)
        if not project:
            raise ResourceNotFoundError("Project", project_id)

        quote = await project_repo.get_quote_by_id(quote_id)
        if not quote or quote.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quote with id {quote_id} not found for project {project_id}",
            )

        role = get_user_role(current_user) or ""
        direct_delete_roles = {"super_admin", "owner", "admin_financiero"}

        # Always clear tentative capacity for this quote when it is removed/deactivated.
        capacity_repo = RepositoryFactory.create_capacity_repository(db, tenant.organization_id)
        await capacity_repo.delete_commitments_by_source(source_type="quote", source_id=quote.id)

        if role in direct_delete_roles:
            # Detach shared proposal links from this quote before hard-delete.
            await db.execute(
                sql_update(ProposalClientLink)
                .where(
                    ProposalClientLink.organization_id == tenant.organization_id,
                    ProposalClientLink.project_id == project_id,
                    ProposalClientLink.quote_id == quote.id,
                )
                .values(quote_id=None)
            )
            # ORM delete keeps relationship cascades for quote items/expenses.
            await db.delete(quote)
            await db.commit()
            return {
                "success": True,
                "action": "deleted",
                "message": "Cotizacion eliminada permanentemente.",
            }

        if role == "product_manager":
            if not _quote_is_active(quote):
                await db.commit()
                return {
                    "success": True,
                    "action": "already_inactive",
                    "message": "La cotizacion ya estaba desactivada.",
                }

            quote.is_active = 0
            quote.deletion_requested_at = datetime.utcnow()
            quote.deletion_requested_by_id = current_user.id
            quote.deletion_request_reason = "Solicitud de Project Manager"
            await db.commit()
            await db.refresh(quote)
            return {
                "success": True,
                "action": "deactivated",
                "message": "Solicitud registrada. La cotizacion fue desactivada y ya no impacta el dashboard.",
            }

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar cotizaciones.",
        )
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError as exc:
        await db.rollback()
        logger.error(f"Integrity error deleting quote {quote_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo eliminar la cotizacion por referencias activas. Intenta desactivarla primero.",
        )
    except Exception as exc:
        await db.rollback()
        logger.error(f"Unexpected error deleting quote {quote_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al eliminar cotizacion",
        )


@router.put("/{project_id}/quotes/{quote_id}", response_model=QuoteResponseWithItems)
async def update_quote(
    project_id: int,
    quote_id: int,
    quote_data: QuoteUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing quote (modifies current version)
    """
    try:
        # Use RepositoryFactory for tenant-scoped access
        project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)
        service_repo = RepositoryFactory.create_service_repository(db, tenant.organization_id)

        # Verify project exists and belongs to tenant (validates ownership)
        project = await project_repo.get_by_id_with_quotes(project_id, include_deleted=False)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found",
            )

        # Get existing quote using repository (validates ownership via project's tenant)
        quote = await project_repo.get_quote_by_id(quote_id)
        if not quote or quote.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Quote with id {quote_id} not found"
            )
        if not _quote_is_active(quote):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This quote is inactive and cannot be updated",
            )

        # Validate services using repository (with tenant scoping)
        service_ids = [item.service_id for item in quote_data.items]
        all_services = await service_repo.get_all(
            where=Service.id.in_(service_ids), include_deleted=False
        )
        # Filter to only active services
        services = {service.id: service for service in all_services if service.is_active}

        requested_service_ids = set(service_ids)
        if len(services) != len(requested_service_ids):
            missing = requested_service_ids - set(services.keys())
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Services with ids {list(missing)} not found or inactive",
            )

        settings_service = SettingsService(db)
        primary_currency = await settings_service.get_primary_currency(tenant.organization_id)
        if project.currency != primary_currency:
            project.currency = primary_currency

        # Calculate blended cost rate
        org_settings = tenant.organization.settings if tenant.organization.settings else {}
        social_config = org_settings.get("social_charges_config") if org_settings else None
        blended_rate = await calculate_blended_cost_rate(
            db,
            primary_currency,
            tenant_id=tenant.organization_id,
            social_charges_config=social_config,
        )

        # Get project taxes (already loaded with get_by_id_with_quotes)
        tax_ids = [tax.id for tax in project.taxes] if project.taxes else []

        # Calculate new totals (using enhanced function - Sprint 14-16)
        items_dict = []
        cell_version_cache: dict[tuple[int, int | None], TeamCellVersion] = {}
        for item in quote_data.items:
            estimated_hours = getattr(item, "estimated_hours", None)
            cell_assignment = getattr(item, "cell_assignment", None)
            if cell_assignment is not None:
                _, _, expanded_total_hours = await _expand_cell_assignment_for_quote(
                    db=db,
                    organization_id=tenant.organization_id,
                    cell_assignment=cell_assignment,
                    cache=cell_version_cache,
                )
                estimated_hours = float(expanded_total_hours)
            item_dict = {
                "service_id": item.service_id,
                "estimated_hours": estimated_hours,
                "pricing_type": getattr(item, "pricing_type", None),
                "fixed_price": getattr(item, "fixed_price", None),
                "quantity": getattr(item, "quantity", 1.0),
                "recurring_price": getattr(item, "recurring_price", None),
                "billing_frequency": getattr(item, "billing_frequency", None),
                "project_value": getattr(item, "project_value", None),
            }
            items_dict.append(item_dict)

        revisions_included = (
            quote_data.revisions_included
            if quote_data.revisions_included is not None
            else (quote.revisions_included if quote.revisions_included else 2)
        )
        revision_cost_per_additional = (
            quote_data.revision_cost_per_additional
            if hasattr(quote_data, "revision_cost_per_additional")
            else quote.revision_cost_per_additional
        )
        target_margin_percentage = getattr(quote_data, "target_margin_percentage", None)
        contingency_description = getattr(quote_data, "contingency_description", None)
        contingency_type = getattr(quote_data, "contingency_type", None)
        contingency_value = getattr(quote_data, "contingency_value", None)

        totals = await calculate_quote_totals_enhanced(
            db,
            items_dict,
            blended_rate,
            tax_ids,
            expenses=None,  # Expenses are managed separately
            target_margin_percentage=target_margin_percentage,
            revisions_included=revisions_included,
            revision_cost_per_additional=revision_cost_per_additional,
            revisions_count=None,
            currency=primary_currency,
            organization_id=tenant.organization_id,
        )
        totals = _apply_contingency_to_totals(totals, contingency_type, contingency_value)

        # Delete old items
        old_items_result = await db.execute(select(QuoteItem).where(QuoteItem.quote_id == quote_id))
        old_items = old_items_result.scalars().all()
        for item in old_items:
            await db.delete(item)

        # Update quote totals (Sprint 16: includes revision fields)
        # ESTÁNDAR NOUGRAM: Convertir float a Decimal para campos Numeric
        from decimal import Decimal

        quote.total_internal_cost = Decimal(str(totals["total_internal_cost"]))
        quote.total_client_price = Decimal(str(totals["total_client_price"]))
        quote.margin_percentage = Decimal(str(totals["margin_percentage"]))
        quote.target_margin_percentage = (
            Decimal(str(target_margin_percentage)) if target_margin_percentage is not None else None
        )  # Update target margin
        quote.contingency_description = contingency_description
        quote.contingency_type = contingency_type
        quote.contingency_value = (
            Decimal(str(contingency_value)) if contingency_value is not None else None
        )
        if quote_data.notes is not None:
            quote.notes = quote_data.notes
        if quote_data.revisions_included is not None:
            quote.revisions_included = quote_data.revisions_included
        if (
            hasattr(quote_data, "revision_cost_per_additional")
            and quote_data.revision_cost_per_additional is not None
        ):
            quote.revision_cost_per_additional = Decimal(
                str(quote_data.revision_cost_per_additional)
            )

        # Create new items using enhanced calculation results (Sprint 14-16)
        quote_items = []
        quote_allocations = []
        quote_cell_assignments = []
        items_breakdown = totals.get("items", [])
        breakdown_map = {item["service_id"]: item for item in items_breakdown}

        for item_data in quote_data.items:
            service = services[item_data.service_id]
            breakdown = breakdown_map.get(item_data.service_id, {})

            # Get calculated values from enhanced breakdown
            # ESTÁNDAR NOUGRAM: Convertir a Decimal para campos Numeric
            internal_cost = Decimal(str(breakdown.get("internal_cost", 0.0)))
            client_price = Decimal(str(breakdown.get("client_price", 0.0)))
            margin_pct = (
                Decimal(str(breakdown.get("margin_percentage", 0.0)))
                if breakdown.get("margin_percentage")
                else Decimal("0")
            )

            # Determine effective pricing type
            effective_pricing_type = (
                getattr(item_data, "pricing_type", None) or service.pricing_type or "hourly"
            )

            # ESTÁNDAR NOUGRAM: Convertir fixed_price a Decimal si existe
            fixed_price_decimal = None
            if getattr(item_data, "fixed_price", None) is not None:
                fixed_price_decimal = Decimal(str(item_data.fixed_price))

            quote_item = QuoteItem(
                quote_id=quote.id,
                service_id=item_data.service_id,
                custom_service_name=(
                    str(getattr(item_data, "custom_service_name", "")).strip() or None
                ),
                estimated_hours=getattr(item_data, "estimated_hours", None),
                pricing_type=effective_pricing_type,
                fixed_price=fixed_price_decimal,
                quantity=getattr(item_data, "quantity", 1.0),
                recurring_price=getattr(item_data, "recurring_price", None),
                billing_frequency=getattr(item_data, "billing_frequency", None),
                project_value=getattr(item_data, "project_value", None),
                internal_cost=internal_cost,
                client_price=client_price,
                margin_percentage=margin_pct,
            )
            quote_items.append(quote_item)

            allocations = getattr(item_data, "allocations", []) or []
            cell_assignment = getattr(item_data, "cell_assignment", None)
            if cell_assignment is not None:
                (
                    version,
                    expanded_allocations,
                    expanded_total_hours,
                ) = await _expand_cell_assignment_for_quote(
                    db=db,
                    organization_id=tenant.organization_id,
                    cell_assignment=cell_assignment,
                    cache=cell_version_cache,
                )
                if getattr(item_data, "estimated_hours", None) is None:
                    quote_item.estimated_hours = expanded_total_hours
                allocations = expanded_allocations
                quote_cell_assignments.append(
                    QuoteItemCellAssignment(
                        quote_item=quote_item,
                        cell_id=version.cell_id,
                        cell_version_id=version.id,
                        occupancy_percentage=cell_assignment.occupancy_percentage,
                        duration_months=int(getattr(cell_assignment, "duration_months", 1) or 1),
                    )
                )

            for alloc in allocations:
                alloc_team_member_id = getattr(alloc, "team_member_id", None)
                alloc_hours = getattr(alloc, "hours", None)
                alloc_role = getattr(alloc, "role", None)
                alloc_start = getattr(alloc, "start_date", None)
                alloc_end = getattr(alloc, "end_date", None)
                if isinstance(alloc, dict):
                    alloc_team_member_id = alloc.get("team_member_id")
                    alloc_hours = alloc.get("hours")
                    alloc_role = alloc.get("role")
                    alloc_start = alloc.get("start_date")
                    alloc_end = alloc.get("end_date")
                quote_allocations.append(
                    QuoteItemAllocation(
                        quote_item=quote_item,
                        team_member_id=alloc_team_member_id,
                        hours=alloc_hours,
                        role=alloc_role,
                        start_date=alloc_start,
                        end_date=alloc_end,
                    )
                )

        db.add_all(quote_items)
        if quote_allocations:
            db.add_all(quote_allocations)
        if quote_cell_assignments:
            db.add_all(quote_cell_assignments)

        # Replace expenses when provided
        if quote_data.expenses is not None:
            await db.execute(sql_delete(QuoteExpense).where(QuoteExpense.quote_id == quote_id))
            for exp_data in quote_data.expenses:
                client_price = exp_data.cost * exp_data.quantity * (1 + exp_data.markup_percentage)
                db.add(
                    QuoteExpense(
                        quote_id=quote_id,
                        name=exp_data.name,
                        description=exp_data.description,
                        cost=exp_data.cost,
                        markup_percentage=exp_data.markup_percentage,
                        category=exp_data.category,
                        quantity=exp_data.quantity,
                        client_price=client_price,
                    )
                )

        await db.commit()
        await db.refresh(quote)

        try:
            capacity_service = CapacityService(db, tenant.organization_id)
            await capacity_service.sync_tentative_from_quote(
                quote_id=quote.id,
                project_id=project_id,
                actor_user_id=current_user.id,
            )
        except Exception as sync_error:
            logger.warning(
                f"Failed to sync tentative capacity on quote update {quote.id}: {sync_error}"
            )

        # Build response
        quote_result = await db.execute(
            select(Quote)
            .where(Quote.id == quote_id)
            .options(
                selectinload(Quote.items).selectinload(QuoteItem.service),
                selectinload(Quote.items).selectinload(QuoteItem.allocations),
                selectinload(Quote.items).selectinload(QuoteItem.cell_assignment),
                selectinload(Quote.expenses),
            )
        )
        updated_quote = quote_result.scalar_one()

        items_response = []
        for item in updated_quote.items:
            items_response.append(
                QuoteItemResponse(
                    id=item.id,
                    service_id=item.service_id,
                    service_name=item.custom_service_name
                    or (item.service.name if item.service else None),
                    custom_service_name=item.custom_service_name,
                    estimated_hours=item.estimated_hours,
                    pricing_type=getattr(item, "pricing_type", None),
                    fixed_price=getattr(item, "fixed_price", None),
                    quantity=getattr(item, "quantity", None),
                    recurring_price=getattr(item, "recurring_price", None),
                    billing_frequency=getattr(item, "billing_frequency", None),
                    project_value=getattr(item, "project_value", None),
                    cell_assignment=(
                        {
                            "id": item.cell_assignment.id,
                            "cell_id": item.cell_assignment.cell_id,
                            "cell_version_id": item.cell_assignment.cell_version_id,
                            "occupancy_percentage": item.cell_assignment.occupancy_percentage,
                            "duration_months": item.cell_assignment.duration_months,
                        }
                        if getattr(item, "cell_assignment", None) is not None
                        else None
                    ),
                    internal_cost=item.internal_cost,
                    client_price=item.client_price,
                    margin_percentage=item.margin_percentage,
                    allocations=[
                        QuoteItemAllocationResponse(
                            id=alloc.id,
                            team_member_id=alloc.team_member_id,
                            hours=alloc.hours,
                            role=alloc.role,
                            start_date=alloc.start_date,
                            end_date=alloc.end_date,
                        )
                        for alloc in (item.allocations or [])
                    ],
                )
            )

        # Invalidate dashboard cache (quotes affect dashboard metrics)
        from app.core.cache import get_cache

        cache = get_cache()
        cache.invalidate_pattern(f"dashboard:{tenant.organization_id}")

        total_taxes, total_with_taxes = _compute_quote_tax_totals(updated_quote, project)

        expenses_response = [
            QuoteExpenseResponse(
                id=exp.id,
                quote_id=exp.quote_id,
                name=exp.name,
                description=exp.description,
                cost=exp.cost,
                markup_percentage=exp.markup_percentage,
                client_price=exp.client_price,
                category=exp.category,
                quantity=exp.quantity,
            )
            for exp in (updated_quote.expenses or [])
        ]

        return QuoteResponseWithItems(
            id=updated_quote.id,
            project_id=updated_quote.project_id,
            version=updated_quote.version,
            total_internal_cost=updated_quote.total_internal_cost,
            total_client_price=updated_quote.total_client_price,
            total_taxes=total_taxes,
            total_with_taxes=total_with_taxes,
            margin_percentage=updated_quote.margin_percentage,
            margin=_build_margin_summary(
                total_client_price=updated_quote.total_client_price,
                total_internal_cost=updated_quote.total_internal_cost,
                total_taxes=total_taxes,
                gross_margin_ratio=updated_quote.margin_percentage,
                target_margin_ratio=updated_quote.target_margin_percentage,
            ),
            contingency_description=getattr(updated_quote, "contingency_description", None),
            contingency_type=getattr(updated_quote, "contingency_type", None),
            contingency_value=getattr(updated_quote, "contingency_value", None),
            notes=updated_quote.notes,
            is_active=bool(getattr(updated_quote, "is_active", 1)),
            deletion_requested_at=getattr(updated_quote, "deletion_requested_at", None),
            deletion_requested_by_id=getattr(updated_quote, "deletion_requested_by_id", None),
            deletion_request_reason=getattr(updated_quote, "deletion_request_reason", None),
            revisions_included=updated_quote.revisions_included
            if hasattr(updated_quote, "revisions_included")
            else 2,
            revision_cost_per_additional=updated_quote.revision_cost_per_additional
            if hasattr(updated_quote, "revision_cost_per_additional")
            else None,
            created_at=updated_quote.created_at,
            updated_at=updated_quote.updated_at,
            items=items_response,
            expenses=expenses_response,
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        import logging
        import traceback

        logging.error(f"Error updating quote {quote_id}: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update quote: {str(e)}",
        )


@router.post(
    "/{project_id}/quotes/{quote_id}/new-version",
    response_model=QuoteResponseWithItems,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_quote_version(
    project_id: int,
    quote_id: int,
    quote_data: QuoteCreateNewVersion,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new version of an existing quote
    Increments version number and creates a new quote record
    Validates ownership via repository tenant scoping
    """
    from app.services.project_service import ProjectService

    try:
        project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)
        quote = await project_repo.get_quote_by_id(quote_id)
        if not quote or quote.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quote with id {quote_id} not found for project {project_id}",
            )
        if not _quote_is_active(quote):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create a new version from an inactive quote",
            )

        project_service = ProjectService(db, tenant.organization_id)
        return await project_service.create_new_quote_version(
            project_id=project_id,
            quote_id=quote_id,
            quote_data=quote_data,
            current_user=current_user,
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating new quote version: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create new quote version: {str(e)}",
        )


@router.get("/{project_id}/quotes/{quote_id}/pdf")
async def download_quote_pdf(
    project_id: int,
    quote_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate and download a PDF version of a quote
    """
    # Verify project belongs to tenant first
    project_check = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.organization_id == tenant.organization_id
        )
    )
    if not project_check.scalar_one_or_none():
        raise ResourceNotFoundError("Project", project_id)

    # Get quote with all relationships (including expenses - Sprint 15)
    result = await db.execute(
        select(Quote)
        .where(Quote.id == quote_id, Quote.project_id == project_id, Quote.is_active == 1)
        .options(
            selectinload(Quote.items).selectinload(QuoteItem.service),
            selectinload(Quote.expenses),  # Sprint 15: Load expenses
            selectinload(Quote.project).selectinload(Project.taxes),
        )
    )
    quote = result.scalar_one_or_none()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote with id {quote_id} for project {project_id} not found",
        )

    # Get project
    project = quote.project
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {project_id} not found"
        )

    # Generate PDF
    try:
        pdf_buffer = generate_quote_pdf(project, quote)

        # Generate filename
        safe_project_name = "".join(
            c for c in project.name if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        filename = f"cotizacion_{safe_project_name}_v{quote.version}.pdf"

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        import logging
        import traceback

        logging.error(f"Error generating PDF for quote {quote_id}: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}",
        )


@router.get("/{project_id}/quotes/{quote_id}/docx")
async def download_quote_docx(
    project_id: int,
    quote_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate and download a DOCX version of a quote
    """
    from app.core.docx_generator import generate_quote_docx

    # Verify project belongs to tenant first
    project_check = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.organization_id == tenant.organization_id
        )
    )
    if not project_check.scalar_one_or_none():
        raise ResourceNotFoundError("Project", project_id)

    # Get quote with all relationships (including expenses - Sprint 15)
    result = await db.execute(
        select(Quote)
        .where(Quote.id == quote_id, Quote.project_id == project_id, Quote.is_active == 1)
        .options(
            selectinload(Quote.items).selectinload(QuoteItem.service),
            selectinload(Quote.expenses),  # Sprint 15: Load expenses
            selectinload(Quote.project).selectinload(Project.taxes),
        )
    )
    quote = result.scalar_one_or_none()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote with id {quote_id} for project {project_id} not found",
        )

    # Get project
    project = quote.project
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {project_id} not found"
        )

    # Generate DOCX
    try:
        docx_buffer = generate_quote_docx(project, quote)

        # Generate filename
        safe_project_name = "".join(
            c for c in project.name if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        filename = f"cotizacion_{safe_project_name}_v{quote.version}.docx"

        return StreamingResponse(
            docx_buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        from app.core.logging import get_logger

        logger = get_logger(__name__)
        logger.error(f"Error generating DOCX for quote {quote_id}", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate DOCX: {str(e)}",
        )


@router.post("/{project_id}/quotes/{quote_id}/send-email", response_model=QuoteEmailResponse)
async def send_quote_email(
    project_id: int,
    quote_id: int,
    email_data: QuoteEmailRequest,
    background_tasks: BackgroundTasks,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(
        get_current_user
    ),  # Permission check inside due to credit consumption logic
    db: AsyncSession = Depends(get_db),
):
    """
    Send quote by email

    **Permissions:**
    - Requires `can_send_quotes` permission
    - Allowed roles: owner, admin_financiero, product_manager, super_admin
    - Denied roles: collaborator (cannot send quotes)

    Requires email provider configuration in environment variables
    (SMTP or MailerSend API).
    """
    # Permission check
    from app.core.permissions import PERM_SEND_QUOTES, check_permission

    try:
        check_permission(current_user, PERM_SEND_QUOTES)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to send quotes"
        )
    from app.core.email import generate_quote_email_html, generate_quote_email_text, send_email
    from app.core.logging import get_logger

    logger = get_logger(__name__)

    # Verify project belongs to tenant first
    project_check = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.organization_id == tenant.organization_id
        )
    )
    if not project_check.scalar_one_or_none():
        raise ResourceNotFoundError("Project", project_id)

    # Get quote with all relationships (including expenses - Sprint 15)
    result = await db.execute(
        select(Quote)
        .where(Quote.id == quote_id, Quote.project_id == project_id, Quote.is_active == 1)
        .options(
            selectinload(Quote.items).selectinload(QuoteItem.service),
            selectinload(Quote.expenses),  # Sprint 15: Load expenses
            selectinload(Quote.project).selectinload(Project.taxes),
        )
    )
    quote = result.scalar_one_or_none()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote with id {quote_id} for project {project_id} not found",
        )

    # Get project
    project = quote.project
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with id {project_id} not found"
        )

    try:
        # Calculate totals
        total_client_price = quote.total_client_price or 0
        taxes = []
        total_taxes = 0
        if hasattr(project, "taxes") and project.taxes:
            for tax in project.taxes:
                tax_amount = (total_client_price * tax.percentage / 100) if tax.percentage else 0
                taxes.append(tax_amount)
                total_taxes += tax_amount

        total_with_taxes = total_client_price + total_taxes

        sender_company_name = (tenant.organization.name or "").strip() or "tu empresa"
        # Generate email subject
        subject = email_data.subject or f'Tienes una Propuesta de "{sender_company_name}"'

        proposal_text = ""
        if email_data.proposal_id is not None:
            proposal_repo = RepositoryFactory.create_proposal_repository(db, tenant.organization_id)
            proposal = await proposal_repo.get_by_id(email_data.proposal_id)
            if not proposal or proposal.project_id != project_id:
                raise HTTPException(status_code=404, detail="Proposal not found for this project")
            proposal_text = _proposal_to_notes_text(
                proposal.body_json if isinstance(proposal.body_json, dict) else {}
            )

        email_notes = (
            proposal_text or email_data.proposal_message or quote.notes or email_data.message
        )

        # Generate email body
        html_body = generate_quote_email_html(
            project_name=project.name,
            client_name=project.client_name,
            quote_version=quote.version,
            total_with_taxes=total_with_taxes,
            currency=project.currency,
            notes=email_notes,
        )

        text_body = generate_quote_email_text(
            project_name=project.name,
            client_name=project.client_name,
            quote_version=quote.version,
            total_with_taxes=total_with_taxes,
            currency=project.currency,
            notes=email_notes,
        )
        # Prepare attachments
        attachments = []

        if email_data.include_pdf:
            pdf_buffer = generate_quote_pdf(project, quote)
            safe_project_name = "".join(
                c for c in project.name if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            pdf_filename = f"cotizacion_{safe_project_name}_v{quote.version}.pdf"
            attachments.append({"filename": pdf_filename, "content": pdf_buffer})

        if email_data.include_docx:
            from app.core.docx_generator import generate_quote_docx

            docx_buffer = generate_quote_docx(project, quote)
            safe_project_name = "".join(
                c for c in project.name if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            docx_filename = f"cotizacion_{safe_project_name}_v{quote.version}.docx"
            attachments.append({"filename": docx_filename, "content": docx_buffer})

        # Update status before queuing email so it's reflected immediately
        if project.status != "Sent":
            project.status = "Sent"
        await db.commit()

        background_tasks.add_task(
            send_email,
            to_email=email_data.to_email,
            subject=subject,
            body_html=html_body,
            body_text=text_body,
            attachments=attachments if attachments else None,
            cc=email_data.cc if email_data.cc else None,
            bcc=email_data.bcc if email_data.bcc else None,
            log_context={
                "email_event": "quote_email",
                "quote_id": quote_id,
                "project_id": project_id,
                "org_id": tenant.organization_id,
            },
        )
        logger.info(
            f"Quote {quote_id} queued for email delivery to {email_data.to_email}",
            user_id=current_user.id,
            project_id=project_id,
        )
        return QuoteEmailResponse(
            success=True, message=f"Quote sent successfully to {email_data.to_email}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error sending quote {quote_id} by email",
            error=str(e),
            user_id=current_user.id,
            project_id=project_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}",
        )
