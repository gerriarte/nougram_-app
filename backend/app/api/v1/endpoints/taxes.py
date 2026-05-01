"""
Tax management endpoints
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError
from app.core.logging import get_logger
from app.core.permission_middleware import require_delete_resources, require_modify_costs
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant_context
from app.models.role import DeleteRequest
from app.models.tax import Tax
from app.models.user import User
from app.repositories.factory import RepositoryFactory
from app.schemas.tax import (
    TaxCreate,
    TaxListResponse,
    TaxResponse,
    TaxUpdate,
)

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=TaxListResponse)
async def list_taxes(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    country: str = None,
    active_only: bool = False,
    include_deleted: bool = False,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
):
    """
    List all taxes with pagination
    Optionally filter by country or active status
    By default, excludes soft-deleted items (deleted_at IS NULL)
    """
    from sqlalchemy import desc

    tax_repo = RepositoryFactory.create_tax_repository(db, tenant.organization_id)

    where_clause = None
    if country or active_only:
        conditions = []
        if country:
            conditions.append(Tax.country == country)
        if active_only:
            conditions.append(Tax.is_active)
        if conditions:
            where_clause = and_(*conditions)

    # Get total count
    total = await tax_repo.count(where=where_clause, include_deleted=include_deleted)

    # Get paginated taxes
    offset = (page - 1) * page_size
    taxes = await tax_repo.get_all(
        where=where_clause,
        include_deleted=include_deleted,
        order_by=desc(Tax.created_at),
        limit=page_size,
        offset=offset,
    )

    # Sort manually since order_by doesn't support tuples
    taxes = sorted(taxes, key=lambda t: (t.country or "", t.name or ""))

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return TaxListResponse(
        items=[TaxResponse.model_validate(tax) for tax in taxes],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/", response_model=TaxResponse, status_code=status.HTTP_201_CREATED)
async def create_tax(
    tax_data: TaxCreate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(
        require_modify_costs
    ),  # Taxes affect costs, so require modify_costs permission
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new tax

    **Permissions:**
    - Requires `can_modify_costs` permission (taxes affect cost calculations)
    - Allowed roles: owner, admin_financiero, super_admin
    - Denied roles: product_manager, collaborator
    """
    user_id = current_user.id  # cache before any await+rollback expiration
    try:
        tax_repo = RepositoryFactory.create_tax_repository(db, tenant.organization_id)

        # Check if code already exists
        existing = await tax_repo.get_by_code(tax_data.code, include_deleted=True)
        if existing:
            if existing.deleted_at is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tax with code '{tax_data.code}' already exists",
                )

            logger.info(
                "Restoring soft-deleted tax with existing code",
                tax_id=existing.id,
                tax_code=tax_data.code,
                user_id=user_id,
            )
            existing.name = tax_data.name
            existing.percentage = tax_data.percentage
            existing.country = tax_data.country
            existing.description = tax_data.description
            existing.is_active = tax_data.is_active
            existing.deleted_at = None
            existing.deleted_by_id = None
            restored_tax = await tax_repo.update(existing)
            return TaxResponse.model_validate(restored_tax)

        logger.info("Creating tax", tax_data=tax_data.model_dump(), user_id=user_id)

        tax_dict = tax_data.model_dump()
        tax_dict["organization_id"] = tenant.organization_id

        new_tax = Tax(**tax_dict)
        new_tax = await tax_repo.create(new_tax)

        logger.info("Tax created successfully", tax_id=new_tax.id, user_id=user_id)
        return TaxResponse.model_validate(new_tax)
    except HTTPException:
        raise
    except IntegrityError as e:
        error_msg = str(e.orig)  # capture before rollback; e.orig is DBAPI-level, no ORM state
        await db.rollback()
        logger.warning(
            "Integrity error creating tax",
            error=error_msg,
            user_id=user_id,
            tax_code=tax_data.code,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tax with code '{tax_data.code}' already exists",
        )
    except Exception as e:
        error_msg = str(e)
        await db.rollback()
        logger.error(
            "Error creating tax",
            error=error_msg,
            user_id=user_id,
            tax_data=tax_data.model_dump(),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tax: {error_msg}",
        )


@router.get("/{tax_id}", response_model=TaxResponse)
async def get_tax(
    tax_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    include_deleted: bool = False,
):
    """
    Get a specific tax by ID
    By default, excludes soft-deleted items
    """
    tax_repo = RepositoryFactory.create_tax_repository(db, tenant.organization_id)
    tax = await tax_repo.get_by_id(tax_id, include_deleted=include_deleted)

    if not tax:
        raise ResourceNotFoundError("Tax", tax_id)

    return TaxResponse.model_validate(tax)


@router.put("/{tax_id}", response_model=TaxResponse)
async def update_tax(
    tax_id: int,
    tax_data: TaxUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(
        require_modify_costs
    ),  # Taxes affect costs, so require modify_costs permission
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing tax
    Cannot update soft-deleted taxes

    **Permissions:**
    - Requires `can_modify_costs` permission (taxes affect cost calculations)
    - Allowed roles: owner, admin_financiero, super_admin
    - Denied roles: product_manager, collaborator
    """

    try:
        tax_repo = RepositoryFactory.create_tax_repository(db, tenant.organization_id)
        tax = await tax_repo.get_by_id(tax_id, include_deleted=False)

        if not tax:
            raise ResourceNotFoundError("Tax", tax_id)

        # Check if code is being updated and if it conflicts (excluding deleted taxes)
        update_data = tax_data.model_dump(exclude_unset=True)
        if "code" in update_data:
            existing = await tax_repo.get_by_code(
                update_data["code"], include_deleted=True, exclude_id=tax_id
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tax with code '{update_data['code']}' already exists",
                )

        logger.info("Updating tax", tax_id=tax_id, update_data=update_data, user_id=current_user.id)
        for field, value in update_data.items():
            setattr(tax, field, value)

        tax = await tax_repo.update(tax)

        logger.info("Tax updated successfully", tax_id=tax_id, user_id=current_user.id)
        return TaxResponse.model_validate(tax)
    except HTTPException:
        raise
    except IntegrityError as e:
        await db.rollback()
        logger.warning(
            "Integrity error updating tax",
            tax_id=tax_id,
            error=str(e),
            user_id=current_user.id,
            update_data=update_data,
        )
        if "code" in update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tax with code '{update_data['code']}' already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tax update failed due to a data integrity constraint",
        )
    except Exception as e:
        await db.rollback()
        logger.error(
            "Error updating tax",
            tax_id=tax_id,
            error=str(e),
            user_id=current_user.id,
            update_data=update_data,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tax: {str(e)}",
        )


@router.delete("/{tax_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tax(
    tax_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(
        require_delete_resources
    ),  # Require permission to delete resources
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete a tax (move to trash)

    **Permissions:**
    - Requires `can_delete_resources` permission
    - Allowed roles: owner, super_admin
    - Denied roles: admin_financiero, product_manager, collaborator
    """
    # Permission is already checked via dependency
    # For now, all users with PERM_DELETE_RESOURCES can delete immediately
    requires_approval = False

    # Verify if the tax exists and is not already deleted
    tax_repo = RepositoryFactory.create_tax_repository(db, tenant.organization_id)
    tax = await tax_repo.get_by_id(tax_id, include_deleted=False)

    if not tax:
        raise ResourceNotFoundError("Tax", tax_id)

    if requires_approval:
        # Create delete request instead of deleting immediately
        delete_request = DeleteRequest(
            resource_type="tax",
            resource_id=tax_id,
            requested_by_id=current_user.id,
            status="pending",  # Use string instead of enum
        )
        db.add(delete_request)
        await db.commit()
        await db.refresh(delete_request)

        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "message": "Delete request created and pending approval",
                "request_id": delete_request.id,
            },
        )

    # Super Admin can delete immediately
    logger.info("Deleting tax", tax_id=tax_id, user_id=current_user.id)
    tax.deleted_at = datetime.utcnow()
    tax.deleted_by_id = current_user.id
    await tax_repo.update(tax)

    return None


@router.post("/{tax_id}/restore", response_model=TaxResponse)
async def restore_tax(
    tax_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Restore a soft-deleted tax from trash
    """
    tax_repo = RepositoryFactory.create_tax_repository(db, tenant.organization_id)
    tax = await tax_repo.get_by_id(tax_id, include_deleted=True)

    if not tax or tax.deleted_at is None:
        raise ResourceNotFoundError("Tax", tax_id)

    # Restore: clear deleted fields
    tax.deleted_at = None
    tax.deleted_by_id = None
    tax = await tax_repo.update(tax)

    return TaxResponse.model_validate(tax)


@router.get("/trash/list", response_model=TaxListResponse)
async def list_deleted_taxes(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List soft-deleted taxes (trash) for the current organization only.
    """
    from sqlalchemy.orm import selectinload

    query = (
        select(Tax)
        .where(
            Tax.deleted_at.isnot(None),
            Tax.organization_id == tenant.organization_id,
        )
        .options(selectinload(Tax.deleted_by))
        .order_by(Tax.deleted_at.desc())
    )

    result = await db.execute(query)
    taxes = result.scalars().all()

    # Build response with user info
    items = []
    for tax in taxes:
        tax_dict = {
            "id": tax.id,
            "name": tax.name,
            "code": tax.code,
            "percentage": tax.percentage,
            "country": tax.country,
            "description": tax.description,
            "is_active": tax.is_active,
            "created_at": tax.created_at,
            "updated_at": tax.updated_at,
            "deleted_at": tax.deleted_at,
            "deleted_by_id": tax.deleted_by_id,
            "deleted_by_name": tax.deleted_by.name if tax.deleted_by else None,
            "deleted_by_email": tax.deleted_by.email if tax.deleted_by else None,
        }
        items.append(TaxResponse.model_validate(tax_dict))

    return TaxListResponse(items=items, total=len(taxes))


@router.delete("/{tax_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def permanently_delete_tax(
    tax_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(
        require_delete_resources
    ),  # Require permission to delete resources
    db: AsyncSession = Depends(get_db),
):
    """
    Permanently delete a soft-deleted tax (hard delete)
    This action cannot be undone. Only soft-deleted taxes can be permanently deleted.

    **Permissions:**
    - Requires `can_delete_resources` permission
    - Allowed roles: owner, super_admin
    - Denied roles: admin_financiero, product_manager, collaborator
    """
    # Verify if the tax exists and is soft-deleted
    tax_repo = RepositoryFactory.create_tax_repository(db, tenant.organization_id)
    tax = await tax_repo.get_by_id(tax_id, include_deleted=True)

    if not tax or tax.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tax with id {tax_id} not found in trash. Only soft-deleted taxes can be permanently deleted.",
        )

    # Hard delete: permanently remove from database
    logger.info("Permanently deleting tax", tax_id=tax_id, user_id=current_user.id)
    await tax_repo.delete(tax, soft=False)

    return None
