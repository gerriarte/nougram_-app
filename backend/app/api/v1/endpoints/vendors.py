"""
Vendor catalog CRUD endpoints — tenant-scoped directory of recurring third-party providers.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant_context
from app.models.user import User
from app.models.vendor import Vendor
from app.repositories.vendor_repository import VendorRepository
from app.schemas.vendor import VendorCreate, VendorListResponse, VendorResponse, VendorUpdate

router = APIRouter()


def _get_repo(db: AsyncSession, tenant: TenantContext) -> VendorRepository:
    return VendorRepository(db, tenant_id=tenant.organization_id)


@router.get("/", response_model=VendorListResponse)
async def list_vendors(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    active_only: bool = False,
    include_deleted: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    repo = _get_repo(db, tenant)
    total = await repo.count(
        where=Vendor.is_active.is_(True) if active_only else None,
        include_deleted=include_deleted,
    )
    offset = (page - 1) * page_size
    vendors = await repo.get_all(
        where=Vendor.is_active.is_(True) if active_only else None,
        include_deleted=include_deleted,
        order_by=desc(Vendor.name),
        limit=page_size,
        offset=offset,
    )
    total_pages = max(1, (total + page_size - 1) // page_size)
    return VendorListResponse(
        items=[VendorResponse.model_validate(v) for v in vendors],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    data: VendorCreate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = _get_repo(db, tenant)
    vendor = Vendor(
        organization_id=tenant.organization_id,
        name=data.name,
        description=data.description,
        category=data.category,
        default_cost=data.default_cost,
        default_markup_percentage=data.default_markup_percentage,
        is_active=data.is_active,
    )
    return VendorResponse.model_validate(await repo.create(vendor))


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = _get_repo(db, tenant)
    vendor = await repo.get_by_id(vendor_id)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    return VendorResponse.model_validate(vendor)


@router.patch("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: int,
    data: VendorUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = _get_repo(db, tenant)
    vendor = await repo.get_by_id(vendor_id)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(vendor, field, value)
    return VendorResponse.model_validate(await repo.update(vendor))


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor(
    vendor_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = _get_repo(db, tenant)
    vendor = await repo.get_by_id(vendor_id)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    vendor.deleted_at = datetime.utcnow()
    vendor.deleted_by_id = current_user.id
    await repo.update(vendor)
