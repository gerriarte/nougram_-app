"""
Team groups/cells endpoints for reusable staffing structures.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.permission_middleware import require_modify_costs, require_view_sensitive_data
from app.core.tenant import TenantContext, get_tenant_context
from app.models.user import User
from app.repositories.factory import RepositoryFactory
from app.schemas.team_cells import (
    TeamCellCreate,
    TeamCellListResponse,
    TeamCellPublishVersionRequest,
    TeamCellResponse,
    TeamCellUpdate,
    TeamCellVersionListResponse,
    TeamCellVersionResponse,
    TeamGroupCreate,
    TeamGroupListResponse,
    TeamGroupResponse,
    TeamGroupUpdate,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/team-groups", response_model=TeamGroupListResponse)
async def list_team_groups(
    include_inactive: bool = Query(False),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_sensitive_data),
    db: AsyncSession = Depends(get_db),
):
    repo = RepositoryFactory.create_team_cell_repository(db, tenant.organization_id)
    groups = await repo.list_groups(include_inactive=include_inactive)
    return TeamGroupListResponse(
        items=[TeamGroupResponse.model_validate(group) for group in groups],
        total=len(groups),
    )


@router.post("/team-groups", response_model=TeamGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_team_group(
    payload: TeamGroupCreate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs),
    db: AsyncSession = Depends(get_db),
):
    repo = RepositoryFactory.create_team_cell_repository(db, tenant.organization_id)
    try:
        group = await repo.create_group(
            name=payload.name,
            description=payload.description,
            is_active=payload.is_active,
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A group with this name already exists in your organization.",
        )
    logger.info("Team group created", group_id=group.id, user_id=current_user.id, organization_id=tenant.organization_id)
    return TeamGroupResponse.model_validate(group)


@router.put("/team-groups/{group_id}", response_model=TeamGroupResponse)
async def update_team_group(
    group_id: int,
    payload: TeamGroupUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs),
    db: AsyncSession = Depends(get_db),
):
    repo = RepositoryFactory.create_team_cell_repository(db, tenant.organization_id)
    group = await repo.get_group(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team group not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(group, field, value)

    try:
        group = await repo.update_group(group)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A group with this name already exists in your organization.",
        )
    logger.info("Team group updated", group_id=group.id, user_id=current_user.id, organization_id=tenant.organization_id)
    return TeamGroupResponse.model_validate(group)


@router.delete("/team-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team_group(
    group_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs),
    db: AsyncSession = Depends(get_db),
):
    repo = RepositoryFactory.create_team_cell_repository(db, tenant.organization_id)
    group = await repo.get_group(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team group not found")
    group.is_active = False
    await repo.update_group(group)
    logger.info("Team group deactivated", group_id=group.id, user_id=current_user.id, organization_id=tenant.organization_id)
    return None


@router.get("/team-cells", response_model=TeamCellListResponse)
async def list_team_cells(
    group_id: int | None = Query(None, gt=0),
    include_inactive: bool = Query(False),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_sensitive_data),
    db: AsyncSession = Depends(get_db),
):
    repo = RepositoryFactory.create_team_cell_repository(db, tenant.organization_id)
    if group_id is not None and not await repo.get_group(group_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team group not found")
    cells = await repo.list_cells(group_id=group_id, include_inactive=include_inactive)
    return TeamCellListResponse(
        items=[TeamCellResponse.model_validate(cell) for cell in cells],
        total=len(cells),
    )


@router.post("/team-cells", response_model=TeamCellResponse, status_code=status.HTTP_201_CREATED)
async def create_team_cell(
    payload: TeamCellCreate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs),
    db: AsyncSession = Depends(get_db),
):
    repo = RepositoryFactory.create_team_cell_repository(db, tenant.organization_id)
    if not await repo.get_group(payload.group_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team group not found")
    try:
        cell = await repo.create_cell(
            group_id=payload.group_id,
            name=payload.name,
            description=payload.description,
            is_active=payload.is_active,
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A cell with this name already exists in the selected group.",
        )
    logger.info("Team cell created", cell_id=cell.id, user_id=current_user.id, organization_id=tenant.organization_id)
    return TeamCellResponse.model_validate(cell)


@router.put("/team-cells/{cell_id}", response_model=TeamCellResponse)
async def update_team_cell(
    cell_id: int,
    payload: TeamCellUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs),
    db: AsyncSession = Depends(get_db),
):
    repo = RepositoryFactory.create_team_cell_repository(db, tenant.organization_id)
    cell = await repo.get_cell(cell_id)
    if not cell:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team cell not found")

    updates = payload.model_dump(exclude_unset=True)
    new_group_id = updates.get("group_id")
    if new_group_id is not None and not await repo.get_group(new_group_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team group not found")

    for field, value in updates.items():
        setattr(cell, field, value)

    try:
        cell = await repo.update_cell(cell)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A cell with this name already exists in the selected group.",
        )
    logger.info("Team cell updated", cell_id=cell.id, user_id=current_user.id, organization_id=tenant.organization_id)
    return TeamCellResponse.model_validate(cell)


@router.delete("/team-cells/{cell_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team_cell(
    cell_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs),
    db: AsyncSession = Depends(get_db),
):
    repo = RepositoryFactory.create_team_cell_repository(db, tenant.organization_id)
    cell = await repo.get_cell(cell_id)
    if not cell:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team cell not found")
    cell.is_active = False
    await repo.update_cell(cell)
    logger.info("Team cell deactivated", cell_id=cell.id, user_id=current_user.id, organization_id=tenant.organization_id)
    return None


@router.get("/team-cells/{cell_id}/versions", response_model=TeamCellVersionListResponse)
async def list_team_cell_versions(
    cell_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_sensitive_data),
    db: AsyncSession = Depends(get_db),
):
    repo = RepositoryFactory.create_team_cell_repository(db, tenant.organization_id)
    cell = await repo.get_cell(cell_id)
    if not cell:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team cell not found")
    versions = await repo.list_versions(cell_id)
    return TeamCellVersionListResponse(
        items=[TeamCellVersionResponse.model_validate(version) for version in versions],
        total=len(versions),
    )


@router.post("/team-cells/{cell_id}/publish-version", response_model=TeamCellVersionResponse)
async def publish_team_cell_version(
    cell_id: int,
    payload: TeamCellPublishVersionRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs),
    db: AsyncSession = Depends(get_db),
):
    repo = RepositoryFactory.create_team_cell_repository(db, tenant.organization_id)
    cell = await repo.get_cell(cell_id)
    if not cell:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team cell not found")

    member_ids = [item.team_member_id for item in payload.members]
    valid_members = await repo.validate_members_belong_to_tenant(member_ids)
    if len(valid_members) != len(set(member_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more team members are invalid, inactive, or outside your organization.",
        )

    version = await repo.publish_version(
        cell=cell,
        members_payload=[item.model_dump() for item in payload.members],
        notes=payload.notes,
        published_by=current_user.id,
    )
    logger.info(
        "Team cell version published",
        cell_id=cell.id,
        version_id=version.id,
        user_id=current_user.id,
        organization_id=tenant.organization_id,
        members_count=len(payload.members),
    )
    return TeamCellVersionResponse.model_validate(version)
