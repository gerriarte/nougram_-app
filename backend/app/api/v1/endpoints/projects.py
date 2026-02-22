"""
Project management endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from io import BytesIO
from datetime import datetime

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant import get_tenant_context, TenantContext
from app.core.calculations import calculate_blended_cost_rate, calculate_quote_totals, calculate_quote_totals_enhanced
from app.core.pdf_generator import generate_quote_pdf
from app.core.exceptions import ResourceNotFoundError
from app.core.permissions import can_create, can_edit, can_delete, PermissionError, get_user_role
from app.core.permission_middleware import require_create_projects
from app.repositories.factory import RepositoryFactory
from app.models.role import DeleteRequest, DeleteRequestStatus
from app.models.project import Project, Quote, QuoteItem, QuoteExpense, project_taxes
from app.models.service import Service
from app.models.tax import Tax
from app.models.user import User
from sqlalchemy import insert, delete as sql_delete
from app.schemas.project import (
    ProjectCreate,
    ProjectCreateWithQuote,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    QuoteResponse,
    QuoteResponseWithItems,
    QuoteItemResponse,
    QuoteItemCreate,
    QuoteUpdate,
    QuoteCreateNewVersion,
    ClientSearchResponse,
)
from app.schemas.quote import QuoteEmailRequest, QuoteEmailResponse, QuoteExpenseCreate, QuoteExpenseResponse

router = APIRouter()


@router.get("/", response_model=ProjectListResponse, summary="List all projects")
async def list_projects(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status_filter: str = None,
    include_deleted: bool = False,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)")
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
            "timestamp": int(time.time() * 1000)
        }
        log_file = Path(r'c:\Users\Usuario\Documents\GitHub\Cotizador\.cursor\debug.log')
        with log_file.open('a', encoding='utf-8') as f:
            f.write(json.dumps(log_data) + '\n')
    except Exception:
        pass
    # #endregion
    
    from fastapi import Query as FastAPIQuery
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
        offset=offset
    )
    
    # Get total count
    total = await project_repo.count(where=where_clause, include_deleted=include_deleted)
    
    # Build response with taxes
    items = []
    for project in projects:
        project_dict = {
            "id": project.id,
            "name": project.name,
            "client_name": project.client_name,
            "client_email": project.client_email,
            "status": project.status,
            "currency": project.currency,
            "tax_ids": [tax.id for tax in project.taxes],
            "taxes": [{"id": tax.id, "name": tax.name, "code": tax.code, "percentage": tax.percentage} for tax in project.taxes],
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }
        items.append(ProjectResponse.model_validate(project_dict))
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return ProjectListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/clients/search", response_model=ClientSearchResponse, summary="Search existing clients")
async def search_clients(
    q: str = Query(..., min_length=2, description="Search query (client name or email)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
    controller = ProjectController(db, tenant, current_user)
    return await controller.search_clients(
        search_query=q,
        limit=limit
    )


@router.post("/", response_model=QuoteResponseWithItems, status_code=status.HTTP_201_CREATED, summary="Create a new project with initial quote")
async def create_project(
    project_data: ProjectCreateWithQuote,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_create_projects),  # Require permission to create projects
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new project with initial quote
    
    **Permissions:**
    - Requires `can_create_projects` permission
    - Allowed roles: owner, admin_financiero, product_manager, collaborator, super_admin
    - Note: Credit consumption is handled inside based on user role
    """
    
    from app.services.project_service import ProjectService
    
    try:
        project_service = ProjectService(db, tenant.organization_id)
        result = await project_service.create_project_with_quote(
            project_data=project_data,
            current_user=current_user,
            subscription_plan=tenant.subscription_plan
        )
        
        # Log audit event
        from app.core.audit import AuditService, AuditAction
        await AuditService.log_action(
            db=db,
            action=AuditAction.PROJECT_CREATE,
            user_id=current_user.id,
            organization_id=tenant.organization_id,
            resource_type="project",
            resource_id=result.project_id,
            request=None,
            details={"project_name": project_data.name, "client_name": project_data.client_name},
            status="success"
        )
        
        # Invalidate dashboard cache (projects affect dashboard metrics)
        from app.core.cache import get_cache
        cache = get_cache()
        cache.invalidate_pattern(f"dashboard:{tenant.organization_id}")
        
        return result
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating project: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get project by ID")
async def get_project(
    project_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    include_deleted: bool = False
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
        "client_name": project.client_name,
        "client_email": project.client_email,
        "status": project.status,
        "currency": project.currency,
        "tax_ids": [tax.id for tax in project.taxes],
        "taxes": [{"id": tax.id, "name": tax.name, "code": tax.code, "percentage": tax.percentage} for tax in project.taxes],
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
    db: AsyncSession = Depends(get_db)
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
    
    # Handle tax_ids separately
    tax_ids = update_data.pop("tax_ids", None)
    
    for field, value in update_data.items():
        setattr(project, field, value)
    
    # Update taxes if provided
    if tax_ids is not None:
        result = await db.execute(
            select(Tax).where(
                Tax.id.in_(tax_ids),
                Tax.is_active == True,
                Tax.deleted_at.is_(None)
            )
        )
        taxes = result.scalars().all()
        if len(taxes) != len(tax_ids):
            missing = set(tax_ids) - {tax.id for tax in taxes}
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Taxes with ids {list(missing)} not found, inactive, or deleted"
            )
        # Remove existing tax associations
        await db.execute(
            sql_delete(project_taxes).where(project_taxes.c.project_id == project_id)
        )
        # Add new tax associations using association table directly
        if taxes:
            await db.execute(
                insert(project_taxes).values([
                    {"project_id": project_id, "tax_id": tax.id}
                    for tax in taxes
                ])
            )
    
    await db.commit()
    
    # Reload project with taxes relationship loaded to avoid lazy loading issues
    project = await project_repo.get_by_id_with_quotes(project_id, include_deleted=False)
    
    # Build response with taxes (now properly loaded)
    project_dict = {
        "id": project.id,
        "name": project.name,
        "client_name": project.client_name,
        "client_email": project.client_email,
        "status": project.status,
        "currency": project.currency,
        "tax_ids": [tax.id for tax in project.taxes],
        "taxes": [{"id": tax.id, "name": tax.name, "code": tax.code, "percentage": tax.percentage} for tax in project.taxes],
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }
    
    return ProjectResponse.model_validate(project_dict)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a project (move to trash)
    Projects are not permanently deleted, allowing restoration
    """
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
            "data": {"project_id": project_id, "tenant_org_id": tenant.organization_id, "user_id": current_user.id},
            "timestamp": int(time.time() * 1000)
        }
        log_file = Path(r'c:\Users\Usuario\Documents\GitHub\Cotizador\.cursor\debug.log')
        with log_file.open('a', encoding='utf-8') as f:
            f.write(json.dumps(log_data) + '\n')
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
    db: AsyncSession = Depends(get_db)
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
        "client_name": project.client_name,
        "client_email": project.client_email,
        "status": project.status,
        "currency": project.currency,
        "tax_ids": [tax.id for tax in project.taxes],
        "taxes": [{"id": tax.id, "name": tax.name, "code": tax.code, "percentage": tax.percentage} for tax in project.taxes],
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }
    
    return ProjectResponse.model_validate(project_dict)


@router.get("/trash/list", response_model=ProjectListResponse)
async def list_deleted_projects(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
        offset=None
    )
    
    # Build response with taxes and user info
    items = []
    for project in projects:
        project_dict = {
            "id": project.id,
            "name": project.name,
            "client_name": project.client_name,
            "client_email": project.client_email,
            "status": project.status,
            "currency": project.currency,
            "tax_ids": [tax.id for tax in project.taxes],
            "taxes": [{"id": tax.id, "name": tax.name, "code": tax.code, "percentage": tax.percentage} for tax in project.taxes],
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "deleted_at": project.deleted_at,
            "deleted_by_id": project.deleted_by_id,
            "deleted_by_name": project.deleted_by.name if project.deleted_by else None,
            "deleted_by_email": project.deleted_by.email if project.deleted_by else None,
        }
        items.append(ProjectResponse.model_validate(project_dict))
    
    return ProjectListResponse(
        items=items,
        total=len(projects)
    )


@router.delete("/{project_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def permanently_delete_project(
    project_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Permanently delete a soft-deleted project (hard delete)
    This action cannot be undone. Only soft-deleted projects can be permanently deleted.
    This will cascade delete all quotes and quote items associated with the project.
    Validates ownership automatically via repository tenant scoping
    """
    # Use RepositoryFactory to get project repository with tenant scoping
    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)
    
    # Get project (including deleted) - repository automatically validates ownership via tenant scoping
    project = await project_repo.get_by_id_with_quotes(project_id, include_deleted=True)
    
    if not project or project.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found in trash. Only soft-deleted projects can be permanently deleted."
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
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific quote with all items
    Validates ownership via repository tenant scoping
    """
    # Use RepositoryFactory to get project repository with tenant scoping
    project_repo = RepositoryFactory.create_project_repository(db, tenant.organization_id)
    
    # Verify project exists and belongs to tenant (validates ownership)
    project = await project_repo.get_by_id(project_id, include_deleted=False)
    if not project:
        raise ResourceNotFoundError("Project", project_id)
    
    # Get quote using repository method (validates ownership via project's tenant)
    quote = await project_repo.get_quote_by_id(quote_id)
    
    if not quote or quote.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote with id {quote_id} for project {project_id} not found"
        )
    
    # Build items response with service names
    items_response = []
    for item in quote.items:
        items_response.append(QuoteItemResponse(
            id=item.id,
            service_id=item.service_id,
            service_name=item.service.name if item.service else None,
            estimated_hours=item.estimated_hours,
                pricing_type=getattr(item, 'pricing_type', None),
                fixed_price=getattr(item, 'fixed_price', None),
                quantity=getattr(item, 'quantity', None),
                recurring_price=getattr(item, 'recurring_price', None),
                billing_frequency=getattr(item, 'billing_frequency', None),
                project_value=getattr(item, 'project_value', None),
            internal_cost=item.internal_cost,
            client_price=item.client_price,
            margin_percentage=item.margin_percentage
        ))
    
    return QuoteResponseWithItems(
        id=quote.id,
        project_id=quote.project_id,
        version=quote.version,
        total_internal_cost=quote.total_internal_cost,
        total_client_price=quote.total_client_price,
        margin_percentage=quote.margin_percentage,
        notes=quote.notes,
        created_at=quote.created_at,
        updated_at=quote.updated_at,
        items=items_response
    )


@router.get("/{project_id}/quotes", response_model=list[QuoteResponse])
async def list_project_quotes(
    project_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
    
    # Get quotes from project relationship (already loaded with get_by_id_with_quotes)
    # Sort by version descending
    quotes = sorted(project.quotes, key=lambda q: q.version, reverse=True)
    
    return [QuoteResponse.model_validate(quote) for quote in quotes]


@router.put("/{project_id}/quotes/{quote_id}", response_model=QuoteResponseWithItems)
async def update_quote(
    project_id: int,
    quote_id: int,
    quote_data: QuoteUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
                detail=f"Project with id {project_id} not found"
            )
        
        # Get existing quote using repository (validates ownership via project's tenant)
        quote = await project_repo.get_quote_by_id(quote_id)
        if not quote or quote.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quote with id {quote_id} not found"
            )
        
        # Validate services using repository (with tenant scoping)
        service_ids = [item.service_id for item in quote_data.items]
        all_services = await service_repo.get_all(
            where=Service.id.in_(service_ids),
            include_deleted=False
        )
        # Filter to only active services
        services = {service.id: service for service in all_services if service.is_active}
        
        if len(services) != len(service_ids):
            missing = set(service_ids) - set(services.keys())
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Services with ids {list(missing)} not found or inactive"
            )
        
        # Calculate blended cost rate
        org_settings = tenant.organization.settings if tenant.organization.settings else {}
        social_config = org_settings.get('social_charges_config') if org_settings else None
        blended_rate = await calculate_blended_cost_rate(
            db, 
            project.currency, 
            tenant_id=tenant.organization_id,
            social_charges_config=social_config
        )
        
        # Get project taxes (already loaded with get_by_id_with_quotes)
        tax_ids = [tax.id for tax in project.taxes] if project.taxes else []
        
        # Calculate new totals (using enhanced function - Sprint 14-16)
        items_dict = []
        for item in quote_data.items:
            item_dict = {
                "service_id": item.service_id,
                "estimated_hours": getattr(item, 'estimated_hours', None),
                "pricing_type": getattr(item, 'pricing_type', None),
                "fixed_price": getattr(item, 'fixed_price', None),
                "quantity": getattr(item, 'quantity', 1.0),
                "recurring_price": getattr(item, 'recurring_price', None),
                "billing_frequency": getattr(item, 'billing_frequency', None),
                "project_value": getattr(item, 'project_value', None),
            }
            items_dict.append(item_dict)
        
        revisions_included = quote_data.revisions_included if quote_data.revisions_included is not None else (quote.revisions_included if quote.revisions_included else 2)
        revision_cost_per_additional = quote_data.revision_cost_per_additional if hasattr(quote_data, 'revision_cost_per_additional') else quote.revision_cost_per_additional
        target_margin_percentage = getattr(quote_data, 'target_margin_percentage', None)
        # Convert Decimal to float for target_margin_percentage (function expects float)
        from decimal import Decimal
        target_margin_float = float(target_margin_percentage) if target_margin_percentage is not None and isinstance(target_margin_percentage, Decimal) else target_margin_percentage
        
        totals = await calculate_quote_totals_enhanced(
            db, 
            items_dict, 
            blended_rate, 
            tax_ids,
            expenses=None,  # Expenses are managed separately
            target_margin_percentage=target_margin_float,  # Pass target margin as float
            revisions_included=revisions_included,
            revision_cost_per_additional=revision_cost_per_additional,
            revisions_count=None,
            currency=project.currency  # ESTÁNDAR NOUGRAM: Pasar moneda del proyecto para precisión
        )
        
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
        quote.target_margin_percentage = Decimal(str(target_margin_percentage)) if target_margin_percentage is not None else None  # Update target margin
        if quote_data.notes is not None:
            quote.notes = quote_data.notes
        if quote_data.revisions_included is not None:
            quote.revisions_included = quote_data.revisions_included
        if hasattr(quote_data, 'revision_cost_per_additional') and quote_data.revision_cost_per_additional is not None:
            quote.revision_cost_per_additional = Decimal(str(quote_data.revision_cost_per_additional))
        
        # Create new items using enhanced calculation results (Sprint 14-16)
        quote_items = []
        items_breakdown = totals.get("items", [])
        breakdown_map = {item["service_id"]: item for item in items_breakdown}
        
        for item_data in quote_data.items:
            service = services[item_data.service_id]
            breakdown = breakdown_map.get(item_data.service_id, {})
            
            # Get calculated values from enhanced breakdown
            # ESTÁNDAR NOUGRAM: Convertir a Decimal para campos Numeric
            internal_cost = Decimal(str(breakdown.get("internal_cost", 0.0)))
            client_price = Decimal(str(breakdown.get("client_price", 0.0)))
            margin_pct = Decimal(str(breakdown.get("margin_percentage", 0.0))) if breakdown.get("margin_percentage") else Decimal('0')
            
            # Determine effective pricing type
            effective_pricing_type = getattr(item_data, 'pricing_type', None) or service.pricing_type or "hourly"
            
            # ESTÁNDAR NOUGRAM: Convertir fixed_price a Decimal si existe
            fixed_price_decimal = None
            if getattr(item_data, 'fixed_price', None) is not None:
                fixed_price_decimal = Decimal(str(item_data.fixed_price))
            
            quote_item = QuoteItem(
                quote_id=quote.id,
                service_id=item_data.service_id,
                estimated_hours=getattr(item_data, 'estimated_hours', None),
                pricing_type=effective_pricing_type,
                fixed_price=fixed_price_decimal,
                quantity=getattr(item_data, 'quantity', 1.0),
                internal_cost=internal_cost,
                client_price=client_price,
                margin_percentage=margin_pct
            )
            quote_items.append(quote_item)
        
        db.add_all(quote_items)
        await db.commit()
        await db.refresh(quote)
        
        # Build response
        quote_result = await db.execute(
            select(Quote)
            .where(Quote.id == quote_id)
            .options(selectinload(Quote.items).selectinload(QuoteItem.service))
        )
        updated_quote = quote_result.scalar_one()
        
        items_response = []
        for item in updated_quote.items:
            items_response.append(QuoteItemResponse(
                id=item.id,
                service_id=item.service_id,
                service_name=item.service.name if item.service else None,
                estimated_hours=item.estimated_hours,
                pricing_type=getattr(item, 'pricing_type', None),
                fixed_price=getattr(item, 'fixed_price', None),
                quantity=getattr(item, 'quantity', None),
                recurring_price=getattr(item, 'recurring_price', None),
                billing_frequency=getattr(item, 'billing_frequency', None),
                project_value=getattr(item, 'project_value', None),
                internal_cost=item.internal_cost,
                client_price=item.client_price,
                margin_percentage=item.margin_percentage
            ))
        
        # Invalidate dashboard cache (quotes affect dashboard metrics)
        from app.core.cache import get_cache
        cache = get_cache()
        cache.invalidate_pattern(f"dashboard:{tenant.organization_id}")
        
        return QuoteResponseWithItems(
            id=updated_quote.id,
            project_id=updated_quote.project_id,
            version=updated_quote.version,
            total_internal_cost=updated_quote.total_internal_cost,
            total_client_price=updated_quote.total_client_price,
            margin_percentage=updated_quote.margin_percentage,
            notes=updated_quote.notes,
            revisions_included=updated_quote.revisions_included if hasattr(updated_quote, 'revisions_included') else 2,
            revision_cost_per_additional=updated_quote.revision_cost_per_additional if hasattr(updated_quote, 'revision_cost_per_additional') else None,
            created_at=updated_quote.created_at,
            updated_at=updated_quote.updated_at,
            items=items_response
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
            detail=f"Failed to update quote: {str(e)}"
        )


@router.post("/{project_id}/quotes/{quote_id}/new-version", response_model=QuoteResponseWithItems, status_code=status.HTTP_201_CREATED)
async def create_new_quote_version(
    project_id: int,
    quote_id: int,
    quote_data: QuoteCreateNewVersion,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new version of an existing quote
    Increments version number and creates a new quote record
    Validates ownership via repository tenant scoping
    """
    from app.services.project_service import ProjectService
    
    try:
        project_service = ProjectService(db, tenant.organization_id)
        return await project_service.create_new_quote_version(
            project_id=project_id,
            quote_id=quote_id,
            quote_data=quote_data,
            current_user=current_user
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating new quote version: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create new quote version: {str(e)}"
        )


@router.get("/{project_id}/quotes/{quote_id}/pdf")
async def download_quote_pdf(
    project_id: int,
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate and download a PDF version of a quote
    """
    # Verify project belongs to tenant first
    project_check = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == tenant.organization_id
        )
    )
    if not project_check.scalar_one_or_none():
        raise ResourceNotFoundError("Project", project_id)
    
    # Get quote with all relationships (including expenses - Sprint 15)
    result = await db.execute(
        select(Quote)
        .where(Quote.id == quote_id, Quote.project_id == project_id)
        .options(
            selectinload(Quote.items).selectinload(QuoteItem.service),
            selectinload(Quote.expenses),  # Sprint 15: Load expenses
            selectinload(Quote.project).selectinload(Project.taxes)
        )
    )
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote with id {quote_id} for project {project_id} not found"
        )
    
    # Get project
    project = quote.project
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    # Generate PDF
    try:
        pdf_buffer = generate_quote_pdf(project, quote)
        
        # Generate filename
        safe_project_name = "".join(c for c in project.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"cotizacion_{safe_project_name}_v{quote.version}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        import logging
        import traceback
        logging.error(f"Error generating PDF for quote {quote_id}: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )


@router.get("/{project_id}/quotes/{quote_id}/docx")
async def download_quote_docx(
    project_id: int,
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate and download a DOCX version of a quote
    """
    from app.core.docx_generator import generate_quote_docx
    
    # Verify project belongs to tenant first
    project_check = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == tenant.organization_id
        )
    )
    if not project_check.scalar_one_or_none():
        raise ResourceNotFoundError("Project", project_id)
    
    # Get quote with all relationships (including expenses - Sprint 15)
    result = await db.execute(
        select(Quote)
        .where(Quote.id == quote_id, Quote.project_id == project_id)
        .options(
            selectinload(Quote.items).selectinload(QuoteItem.service),
            selectinload(Quote.expenses),  # Sprint 15: Load expenses
            selectinload(Quote.project).selectinload(Project.taxes)
        )
    )
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote with id {quote_id} for project {project_id} not found"
        )
    
    # Get project
    project = quote.project
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    # Generate DOCX
    try:
        docx_buffer = generate_quote_docx(project, quote)
        
        # Generate filename
        safe_project_name = "".join(c for c in project.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"cotizacion_{safe_project_name}_v{quote.version}.docx"
        
        return StreamingResponse(
            docx_buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error generating DOCX for quote {quote_id}", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate DOCX: {str(e)}"
        )


@router.post("/{project_id}/quotes/{quote_id}/send-email", response_model=QuoteEmailResponse)
async def send_quote_email(
    project_id: int,
    quote_id: int,
    email_data: QuoteEmailRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),  # Permission check inside due to credit consumption logic
    db: AsyncSession = Depends(get_db)
):
    """
    Send quote by email
    
    **Permissions:**
    - Requires `can_send_quotes` permission
    - Allowed roles: owner, admin_financiero, product_manager, super_admin
    - Denied roles: collaborator (cannot send quotes)
    
    Requires SMTP configuration in environment variables.
    """
    # Permission check
    from app.core.permissions import check_permission, PERM_SEND_QUOTES, PermissionError
    try:
        check_permission(current_user, PERM_SEND_QUOTES)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to send quotes"
        )
    from app.core.email import send_email, generate_quote_email_html, generate_quote_email_text
    from app.core.logging import get_logger
    
    logger = get_logger(__name__)
    
    # Verify project belongs to tenant first
    project_check = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == tenant.organization_id
        )
    )
    if not project_check.scalar_one_or_none():
        raise ResourceNotFoundError("Project", project_id)
    
    # Get quote with all relationships (including expenses - Sprint 15)
    result = await db.execute(
        select(Quote)
        .where(Quote.id == quote_id, Quote.project_id == project_id)
        .options(
            selectinload(Quote.items).selectinload(QuoteItem.service),
            selectinload(Quote.expenses),  # Sprint 15: Load expenses
            selectinload(Quote.project).selectinload(Project.taxes)
        )
    )
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote with id {quote_id} for project {project_id} not found"
        )
    
    # Get project
    project = quote.project
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    try:
        # Calculate totals
        total_client_price = quote.total_client_price or 0
        taxes = []
        total_taxes = 0
        if hasattr(project, 'taxes') and project.taxes:
            for tax in project.taxes:
                tax_amount = (total_client_price * tax.percentage / 100) if tax.percentage else 0
                taxes.append(tax_amount)
                total_taxes += tax_amount
        
        total_with_taxes = total_client_price + total_taxes
        
        # Generate email subject
        subject = email_data.subject or f"Quote for {project.name} - Version {quote.version}"
        
        # Generate email body
        html_body = generate_quote_email_html(
            project_name=project.name,
            client_name=project.client_name,
            quote_version=quote.version,
            total_with_taxes=total_with_taxes,
            currency=project.currency,
            notes=quote.notes or email_data.message
        )
        
        text_body = generate_quote_email_text(
            project_name=project.name,
            client_name=project.client_name,
            quote_version=quote.version,
            total_with_taxes=total_with_taxes,
            currency=project.currency,
            notes=quote.notes or email_data.message
        )
        
        # Prepare attachments
        attachments = []
        
        if email_data.include_pdf:
            pdf_buffer = generate_quote_pdf(project, quote)
            safe_project_name = "".join(c for c in project.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            pdf_filename = f"cotizacion_{safe_project_name}_v{quote.version}.pdf"
            attachments.append({
                'filename': pdf_filename,
                'content': pdf_buffer
            })
        
        if email_data.include_docx:
            from app.core.docx_generator import generate_quote_docx
            docx_buffer = generate_quote_docx(project, quote)
            safe_project_name = "".join(c for c in project.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            docx_filename = f"cotizacion_{safe_project_name}_v{quote.version}.docx"
            attachments.append({
                'filename': docx_filename,
                'content': docx_buffer
            })
        
        # Send email
        success = await send_email(
            to_email=email_data.to_email,
            subject=subject,
            body_html=html_body,
            body_text=text_body,
            attachments=attachments if attachments else None,
            cc=email_data.cc if email_data.cc else None,
            bcc=email_data.bcc if email_data.bcc else None
        )
        
        if success:
            logger.info(
                f"Quote {quote_id} sent by email to {email_data.to_email}",
                user_id=current_user.id,
                project_id=project_id
            )
            return QuoteEmailResponse(
                success=True,
                message=f"Quote sent successfully to {email_data.to_email}"
            )
        else:
            logger.error(
                f"Failed to send quote {quote_id} by email",
                user_id=current_user.id,
                project_id=project_id,
                to_email=email_data.to_email
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email. Please check SMTP configuration."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error sending quote {quote_id} by email",
            error=str(e),
            user_id=current_user.id,
            project_id=project_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )




        await db.commit()
        await db.refresh(new_quote)
        
        # Build response
        quote_result = await db.execute(
            select(Quote)
            .where(Quote.id == new_quote.id)
            .options(selectinload(Quote.items).selectinload(QuoteItem.service))
        )
        final_quote = quote_result.scalar_one()
        
        items_response = []
        for item in final_quote.items:
            items_response.append(QuoteItemResponse(
                id=item.id,
                service_id=item.service_id,
                service_name=item.service.name if item.service else None,
                estimated_hours=item.estimated_hours,
                internal_cost=item.internal_cost,
                client_price=item.client_price,
                margin_percentage=item.margin_percentage
            ))
        
        return QuoteResponseWithItems(
            id=final_quote.id,
            project_id=final_quote.project_id,
            version=final_quote.version,
            total_internal_cost=final_quote.total_internal_cost,
            total_client_price=final_quote.total_client_price,
            margin_percentage=final_quote.margin_percentage,
            notes=final_quote.notes,
            revisions_included=final_quote.revisions_included if hasattr(final_quote, 'revisions_included') else 2,
            revision_cost_per_additional=final_quote.revision_cost_per_additional if hasattr(final_quote, 'revision_cost_per_additional') else None,
            created_at=final_quote.created_at,
            updated_at=final_quote.updated_at,
            items=items_response
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        import logging
        import traceback
        logging.error(f"Error creating new quote version: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create new quote version: {str(e)}"
        )


@router.get("/{project_id}/quotes/{quote_id}/pdf")
async def download_quote_pdf(
    project_id: int,
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate and download a PDF version of a quote
    """
    # Verify project belongs to tenant first
    project_check = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == tenant.organization_id
        )
    )
    if not project_check.scalar_one_or_none():
        raise ResourceNotFoundError("Project", project_id)
    
    # Get quote with all relationships (including expenses - Sprint 15)
    result = await db.execute(
        select(Quote)
        .where(Quote.id == quote_id, Quote.project_id == project_id)
        .options(
            selectinload(Quote.items).selectinload(QuoteItem.service),
            selectinload(Quote.expenses),  # Sprint 15: Load expenses
            selectinload(Quote.project).selectinload(Project.taxes)
        )
    )
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote with id {quote_id} for project {project_id} not found"
        )
    
    # Get project
    project = quote.project
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    # Generate PDF
    try:
        pdf_buffer = generate_quote_pdf(project, quote)
        
        # Generate filename
        safe_project_name = "".join(c for c in project.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"cotizacion_{safe_project_name}_v{quote.version}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        import logging
        import traceback
        logging.error(f"Error generating PDF for quote {quote_id}: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )


@router.get("/{project_id}/quotes/{quote_id}/docx")
async def download_quote_docx(
    project_id: int,
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate and download a DOCX version of a quote
    """
    from app.core.docx_generator import generate_quote_docx
    
    # Verify project belongs to tenant first
    project_check = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == tenant.organization_id
        )
    )
    if not project_check.scalar_one_or_none():
        raise ResourceNotFoundError("Project", project_id)
    
    # Get quote with all relationships (including expenses - Sprint 15)
    result = await db.execute(
        select(Quote)
        .where(Quote.id == quote_id, Quote.project_id == project_id)
        .options(
            selectinload(Quote.items).selectinload(QuoteItem.service),
            selectinload(Quote.expenses),  # Sprint 15: Load expenses
            selectinload(Quote.project).selectinload(Project.taxes)
        )
    )
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote with id {quote_id} for project {project_id} not found"
        )
    
    # Get project
    project = quote.project
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    # Generate DOCX
    try:
        docx_buffer = generate_quote_docx(project, quote)
        
        # Generate filename
        safe_project_name = "".join(c for c in project.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"cotizacion_{safe_project_name}_v{quote.version}.docx"
        
        return StreamingResponse(
            docx_buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error generating DOCX for quote {quote_id}", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate DOCX: {str(e)}"
        )


@router.post("/{project_id}/quotes/{quote_id}/send-email", response_model=QuoteEmailResponse)
async def send_quote_email(
    project_id: int,
    quote_id: int,
    email_data: QuoteEmailRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),  # Permission check inside due to credit consumption logic
    db: AsyncSession = Depends(get_db)
):
    """
    Send quote by email
    
    **Permissions:**
    - Requires `can_send_quotes` permission
    - Allowed roles: owner, admin_financiero, product_manager, super_admin
    - Denied roles: collaborator (cannot send quotes)
    
    Requires SMTP configuration in environment variables.
    """
    # Permission check
    from app.core.permissions import check_permission, PERM_SEND_QUOTES, PermissionError
    try:
        check_permission(current_user, PERM_SEND_QUOTES)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to send quotes"
        )
    from app.core.email import send_email, generate_quote_email_html, generate_quote_email_text
    from app.core.logging import get_logger
    
    logger = get_logger(__name__)
    
    # Verify project belongs to tenant first
    project_check = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == tenant.organization_id
        )
    )
    if not project_check.scalar_one_or_none():
        raise ResourceNotFoundError("Project", project_id)
    
    # Get quote with all relationships (including expenses - Sprint 15)
    result = await db.execute(
        select(Quote)
        .where(Quote.id == quote_id, Quote.project_id == project_id)
        .options(
            selectinload(Quote.items).selectinload(QuoteItem.service),
            selectinload(Quote.expenses),  # Sprint 15: Load expenses
            selectinload(Quote.project).selectinload(Project.taxes)
        )
    )
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote with id {quote_id} for project {project_id} not found"
        )
    
    # Get project
    project = quote.project
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    
    try:
        # Calculate totals
        total_client_price = quote.total_client_price or 0
        taxes = []
        total_taxes = 0
        if hasattr(project, 'taxes') and project.taxes:
            for tax in project.taxes:
                tax_amount = (total_client_price * tax.percentage / 100) if tax.percentage else 0
                taxes.append(tax_amount)
                total_taxes += tax_amount
        
        total_with_taxes = total_client_price + total_taxes
        
        # Generate email subject
        subject = email_data.subject or f"Quote for {project.name} - Version {quote.version}"
        
        # Generate email body
        html_body = generate_quote_email_html(
            project_name=project.name,
            client_name=project.client_name,
            quote_version=quote.version,
            total_with_taxes=total_with_taxes,
            currency=project.currency,
            notes=quote.notes or email_data.message
        )
        
        text_body = generate_quote_email_text(
            project_name=project.name,
            client_name=project.client_name,
            quote_version=quote.version,
            total_with_taxes=total_with_taxes,
            currency=project.currency,
            notes=quote.notes or email_data.message
        )
        
        # Prepare attachments
        attachments = []
        
        if email_data.include_pdf:
            pdf_buffer = generate_quote_pdf(project, quote)
            safe_project_name = "".join(c for c in project.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            pdf_filename = f"cotizacion_{safe_project_name}_v{quote.version}.pdf"
            attachments.append({
                'filename': pdf_filename,
                'content': pdf_buffer
            })
        
        if email_data.include_docx:
            from app.core.docx_generator import generate_quote_docx
            docx_buffer = generate_quote_docx(project, quote)
            safe_project_name = "".join(c for c in project.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            docx_filename = f"cotizacion_{safe_project_name}_v{quote.version}.docx"
            attachments.append({
                'filename': docx_filename,
                'content': docx_buffer
            })
        
        # Send email
        success = await send_email(
            to_email=email_data.to_email,
            subject=subject,
            body_html=html_body,
            body_text=text_body,
            attachments=attachments if attachments else None,
            cc=email_data.cc if email_data.cc else None,
            bcc=email_data.bcc if email_data.bcc else None
        )
        
        if success:
            logger.info(
                f"Quote {quote_id} sent by email to {email_data.to_email}",
                user_id=current_user.id,
                project_id=project_id
            )
            return QuoteEmailResponse(
                success=True,
                message=f"Quote sent successfully to {email_data.to_email}"
            )
        else:
            logger.error(
                f"Failed to send quote {quote_id} by email",
                user_id=current_user.id,
                project_id=project_id,
                to_email=email_data.to_email
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email. Please check SMTP configuration."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error sending quote {quote_id} by email",
            error=str(e),
            user_id=current_user.id,
            project_id=project_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )



