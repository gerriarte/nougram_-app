"""
Service catalog endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant import get_tenant_context, TenantContext
from app.core.exceptions import ResourceNotFoundError, ResourceInUseError
from app.core.permissions import can_create, can_edit, can_delete, PermissionError
from app.core.permission_middleware import require_create_services, require_delete_resources
from app.core.logging import get_logger
from app.models.service import Service
from app.models.project import QuoteItem
from app.models.user import User
from app.models.role import DeleteRequest, DeleteRequestStatus
from app.repositories.factory import RepositoryFactory
from app.schemas.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    ServiceListResponse,
)

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=ServiceListResponse, summary="List all services")
async def list_services(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    active_only: bool = False,
    include_deleted: bool = False,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)")
):
    """
    List all services with pagination
    Optionally filter by active status
    By default, excludes soft-deleted items (deleted_at IS NULL)
    """
    from sqlalchemy import desc
    from app.models.service import Service
    
    service_repo = RepositoryFactory.create_service_repository(db, tenant.organization_id)
    offset = (page - 1) * page_size
    
    # Get total count
    if active_only:
        all_services = await service_repo.get_all_active(include_deleted=include_deleted)
        total = len(all_services)
        services = await service_repo.get_all(
            where=Service.is_active == True,
            include_deleted=include_deleted,
            order_by=desc(Service.created_at),
            limit=page_size,
            offset=offset
        )
    else:
        total = await service_repo.count(include_deleted=include_deleted)
        services = await service_repo.get_all(
            include_deleted=include_deleted,
            order_by=desc(Service.created_at),
            limit=page_size,
            offset=offset
        )
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return ServiceListResponse(
        items=[ServiceResponse.model_validate(service) for service in services],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED, summary="Create a new service")
async def create_service(
    service_data: ServiceCreate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_create_services),  # Require permission to create services
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new service
    
    **Permissions:**
    - Requires `can_create_services` permission
    - Allowed roles: owner, admin_financiero, super_admin
    - Denied roles: product_manager, collaborator
    """
    
    # Validate service limit for plan
    from app.core.plan_limits import validate_service_limit
    await validate_service_limit(tenant.organization_id, tenant.subscription_plan, db)
    
    logger.info("Creating service", service_data=service_data.model_dump(), user_id=current_user.id)
    service_dict = service_data.model_dump()
    service_dict['organization_id'] = tenant.organization_id
    new_service = Service(**service_dict)
    service_repo = RepositoryFactory.create_service_repository(db, tenant.organization_id)
    new_service = await service_repo.create(new_service)
    
    # Log audit event
    from app.core.audit import AuditService, AuditAction
    from fastapi import Request
    await AuditService.log_action(
        db=db,
        action=AuditAction.SERVICE_CREATE,
        user_id=current_user.id,
        organization_id=tenant.organization_id,
        resource_type="service",
        resource_id=new_service.id,
        request=None,  # Request not available in this endpoint
        details={"service_name": new_service.name},
        status="success"
    )
    
    # Invalidate dashboard cache (services affect revenue_by_service)
    from app.core.cache import get_cache
    cache = get_cache()
    cache.invalidate_pattern(f"dashboard:{tenant.organization_id}")
    
    logger.info("Service created successfully", service_id=new_service.id, user_id=current_user.id)
    return ServiceResponse.model_validate(new_service)


@router.get("/{service_id}", response_model=ServiceResponse, summary="Get service by ID")
async def get_service(
    service_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    include_deleted: bool = False
):
    """
    Get a specific service by ID (with tenant scoping)
    By default, excludes soft-deleted items
    """
    service_repo = RepositoryFactory.create_service_repository(db, tenant.organization_id)
    service = await service_repo.get_by_id(service_id, include_deleted=include_deleted)
    
    if not service:
        raise ResourceNotFoundError("Service", service_id)
    
    return ServiceResponse.model_validate(service)


@router.put("/{service_id}", response_model=ServiceResponse, summary="Update service")
async def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing service
    Cannot update soft-deleted services
    
    Permissions:
    - Super Admin: Allowed
    - Admin Financiero: Allowed
    - Product Manager: Not allowed
    """
    if not can_edit(current_user, "service"):
        raise PermissionError("You don't have permission to edit services")
    
    try:
        service_repo = RepositoryFactory.create_service_repository(db, tenant.organization_id)
        service = await service_repo.get_by_id(service_id, include_deleted=False)
        
        if not service:
            raise ResourceNotFoundError("Service", service_id)
        
        update_data = service_data.model_dump(exclude_unset=True)
        logger.info("Updating service", service_id=service_id, update_data=update_data, user_id=current_user.id)
        
        for field, value in update_data.items():
            setattr(service, field, value)
        
        service = await service_repo.update(service)
        
        # Invalidate dashboard cache (services affect revenue_by_service)
        from app.core.cache import get_cache
        cache = get_cache()
        cache.invalidate_pattern(f"dashboard:{tenant.organization_id}")
        
        logger.info("Service updated successfully", service_id=service_id, user_id=current_user.id)
        return ServiceResponse.model_validate(service)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "Error updating service",
            service_id=service_id,
            error=str(e),
            user_id=current_user.id,
            update_data=service_data.model_dump(exclude_unset=True) if hasattr(service_data, 'model_dump') else str(service_data),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update service: {str(e)}"
        )


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete service (soft delete)")
async def delete_service(
    service_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a service (move to trash)
    Validates that the service is not being used in any quotes before deletion
    
    **Permissions:**
    - Requires `can_delete_resources` permission
    - Allowed roles: owner, super_admin
    - Denied roles: admin_financiero, product_manager, collaborator
    """
    # Permission check
    from app.core.permissions import check_permission, PERM_DELETE_RESOURCES, PermissionError as PermError
    try:
        check_permission(current_user, PERM_DELETE_RESOURCES)
    except PermError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete services"
        )
    # For now, all users with PERM_DELETE_RESOURCES can delete immediately
    requires_approval = False
    
    # Verify if the service exists and is not already deleted
    service_repo = RepositoryFactory.create_service_repository(db, tenant.organization_id)
    service = await service_repo.get_by_id(service_id, include_deleted=False)
    
    if not service:
        raise ResourceNotFoundError("Service", service_id)
    
    # VALIDATION: Check if the service is in use in any quote items
    usage_result = await db.execute(
        select(func.count(QuoteItem.id))
        .where(QuoteItem.service_id == service_id)
    )
    usage_count = usage_result.scalar() or 0
    
    if usage_count > 0:
        raise ResourceInUseError(
            resource_type="Service",
            resource_name=service.name,
            usage_count=usage_count,
            usage_context="quote item(s)"
        )
    
    if requires_approval:
        # Create delete request instead of deleting immediately
        delete_request = DeleteRequest(
            resource_type="service",
            resource_id=service_id,
            requested_by_id=current_user.id,
            status="pending"  # Use string instead of enum
        )
        db.add(delete_request)
        await db.commit()
        await db.refresh(delete_request)
        
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "message": "Delete request created and pending approval",
                "request_id": delete_request.id
            }
        )
    
    # Super Admin can delete immediately
    service.deleted_at = datetime.utcnow()
    service.deleted_by_id = current_user.id
    await service_repo.update(service)
    
    return None


@router.post("/{service_id}/restore", response_model=ServiceResponse)
async def restore_service(
    service_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Restore a soft-deleted service from trash (with tenant scoping)
    """
    service_repo = RepositoryFactory.create_service_repository(db, tenant.organization_id)
    # Get service including deleted ones
    service = await service_repo.get_by_id(service_id, include_deleted=True)
    
    if not service or service.deleted_at is None:
        raise ResourceNotFoundError("Service", service_id)
    
    # Restore: clear deleted fields
    service.deleted_at = None
    service.deleted_by_id = None
    service = await service_repo.update(service)
    
    return ServiceResponse.model_validate(service)


@router.get("/trash/list", response_model=ServiceListResponse)
async def list_deleted_services(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all soft-deleted services (trash) for the tenant
    """
    from sqlalchemy.orm import selectinload
    
    query = select(Service).where(
        Service.deleted_at.isnot(None),
        Service.organization_id == tenant.organization_id
    ).options(selectinload(Service.deleted_by)).order_by(Service.deleted_at.desc())
    
    result = await db.execute(query)
    services = result.scalars().all()
    
    # Build response with user info
    items = []
    for service in services:
        service_dict = {
            "id": service.id,
            "name": service.name,
            "description": service.description,
            "default_margin_target": service.default_margin_target,
            "is_active": service.is_active,
            "created_at": service.created_at,
            "updated_at": service.updated_at,
            "deleted_at": service.deleted_at,
            "deleted_by_id": service.deleted_by_id,
            "deleted_by_name": service.deleted_by.name if service.deleted_by else None,
            "deleted_by_email": service.deleted_by.email if service.deleted_by else None,
        }
        items.append(ServiceResponse.model_validate(service_dict))
    
    return ServiceListResponse(
        items=items,
        total=len(services)
    )


@router.delete("/{service_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def permanently_delete_service(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Permanently delete a soft-deleted service (hard delete)
    This action cannot be undone. Only soft-deleted services can be permanently deleted.
    """
    # Verify if the service exists and is soft-deleted
    result = await db.execute(
        select(Service).where(
            Service.id == service_id,
            Service.deleted_at.isnot(None)
        )
    )
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with id {service_id} not found in trash. Only soft-deleted services can be permanently deleted."
        )
    
    # Hard delete: permanently remove from database
    await db.delete(service)
    await db.commit()
    
    return None
