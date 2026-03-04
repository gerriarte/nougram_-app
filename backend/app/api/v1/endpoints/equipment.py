"""
Equipment amortization management endpoints.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BusinessLogicError, ResourceNotFoundError
from app.core.logging import get_logger
from app.core.permission_middleware import require_modify_costs, require_view_sensitive_data
from app.core.tenant import TenantContext, get_tenant_context
from app.models.equipment import EquipmentAmortization
from app.models.user import User
from app.repositories.factory import RepositoryFactory
from app.schemas.equipment import (
    EquipmentCreate,
    EquipmentListResponse,
    EquipmentResponse,
    EquipmentUpdate,
)

router = APIRouter()
logger = get_logger(__name__)


def _validate_salvage(purchase_price, salvage_value):
    if salvage_value is not None and purchase_price is not None and salvage_value > purchase_price:
        raise BusinessLogicError("salvage_value cannot be greater than purchase_price")


@router.get("/equipment", response_model=EquipmentListResponse)
async def list_equipment(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_sensitive_data),
    db: AsyncSession = Depends(get_db),
    include_deleted: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    repo = RepositoryFactory.create_equipment_repository(db, tenant.organization_id)
    total = await repo.count(include_deleted=include_deleted)
    offset = (page - 1) * page_size
    items = await repo.get_all(
        include_deleted=include_deleted,
        order_by=EquipmentAmortization.created_at.desc(),
        limit=page_size,
        offset=offset,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    logger.info("Equipment listed", user_id=current_user.id, count=len(items), total=total)
    return EquipmentListResponse(
        items=[EquipmentResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/equipment", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_equipment(
    payload: EquipmentCreate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs),
    db: AsyncSession = Depends(get_db),
):
    _validate_salvage(payload.purchase_price, payload.salvage_value)
    repo = RepositoryFactory.create_equipment_repository(db, tenant.organization_id)
    entity = EquipmentAmortization(
        organization_id=tenant.organization_id,
        **payload.model_dump(),
    )
    created = await repo.create(entity)
    logger.info("Equipment created", user_id=current_user.id, equipment_id=created.id)
    return EquipmentResponse.model_validate(created)


@router.put("/equipment/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: int,
    payload: EquipmentUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs),
    db: AsyncSession = Depends(get_db),
):
    repo = RepositoryFactory.create_equipment_repository(db, tenant.organization_id)
    entity = await repo.get_by_id(equipment_id, include_deleted=False)
    if not entity:
        raise ResourceNotFoundError("Equipment", equipment_id)

    updates = payload.model_dump(exclude_unset=True)
    next_purchase_price = updates.get("purchase_price", entity.purchase_price)
    next_salvage_value = updates.get("salvage_value", entity.salvage_value)
    _validate_salvage(next_purchase_price, next_salvage_value)

    for field, value in updates.items():
        setattr(entity, field, value)

    updated = await repo.update(entity)
    logger.info("Equipment updated", user_id=current_user.id, equipment_id=equipment_id)
    return EquipmentResponse.model_validate(updated)


@router.delete("/equipment/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment(
    equipment_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs),
    db: AsyncSession = Depends(get_db),
):
    repo = RepositoryFactory.create_equipment_repository(db, tenant.organization_id)
    entity = await repo.get_by_id(equipment_id, include_deleted=False)
    if not entity:
        raise ResourceNotFoundError("Equipment", equipment_id)

    await repo.delete(entity, soft=True, deleted_by_id=current_user.id)
    logger.info("Equipment deleted", user_id=current_user.id, equipment_id=equipment_id)
