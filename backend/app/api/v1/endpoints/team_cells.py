"""
Team groups/cells endpoints for reusable staffing structures.
"""
from datetime import date, datetime, time, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.permission_middleware import require_modify_costs, require_view_sensitive_data
from app.core.tenant import TenantContext, get_tenant_context
from app.models.capacity import CapacityCommitment
from app.models.team import TeamMember
from app.models.team_cells import TeamCell
from app.models.user import User
from app.repositories.factory import RepositoryFactory
from app.schemas.team_cells import (
    CapacityCellOverviewResponse,
    CapacityMemberOverviewResponse,
    CapacityOverviewResponse,
    CapacityTotalsResponse,
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


def _to_period_bounds(period_start: date, period_end: date) -> tuple[datetime, datetime]:
    start = datetime.combine(period_start, time.min).replace(tzinfo=timezone.utc)
    end = datetime.combine(period_end, time.max).replace(tzinfo=timezone.utc)
    return start, end


@router.get("/capacity/overview", response_model=CapacityOverviewResponse)
async def get_capacity_overview(
    period_start: date = Query(..., description="Period start date (YYYY-MM-DD)"),
    period_end: date = Query(..., description="Period end date (YYYY-MM-DD)"),
    states: list[str] = Query(default=["tentative", "committed", "actual"]),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_sensitive_data),
    db: AsyncSession = Depends(get_db),
):
    if period_end < period_start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="period_end must be >= period_start")

    normalized_states = [s.strip().lower() for s in (states or []) if str(s).strip()]
    if not normalized_states:
        normalized_states = ["tentative", "committed", "actual"]
    allowed_states = {"tentative", "committed", "actual"}
    if any(s not in allowed_states for s in normalized_states):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state value. Allowed: tentative, committed, actual",
        )

    period_start_dt, period_end_dt = _to_period_bounds(period_start, period_end)
    months_count = ((period_end.year - period_start.year) * 12) + (period_end.month - period_start.month) + 1
    months_count = max(1, months_count)

    active_members_result = await db.execute(
        select(TeamMember).where(
            TeamMember.organization_id == tenant.organization_id,
            TeamMember.is_active == True,
        )
    )
    active_members = active_members_result.scalars().all()

    member_hours_result = await db.execute(
        select(
            CapacityCommitment.team_member_id,
            CapacityCommitment.state,
            func.sum(CapacityCommitment.hours).label("hours_sum"),
        )
        .where(
            CapacityCommitment.organization_id == tenant.organization_id,
            CapacityCommitment.state.in_(normalized_states),
            CapacityCommitment.period_start <= period_end_dt,
            CapacityCommitment.period_end >= period_start_dt,
        )
        .group_by(CapacityCommitment.team_member_id, CapacityCommitment.state)
    )
    member_hours_rows = member_hours_result.all()
    member_state_hours: dict[int, dict[str, Decimal]] = {}
    for team_member_id, state_name, hours_sum in member_hours_rows:
        member_state_hours.setdefault(team_member_id, {})[state_name] = Decimal(str(hours_sum or 0))

    members_response: list[CapacityMemberOverviewResponse] = []
    for member in active_members:
        states_dict = member_state_hours.get(member.id, {})
        tentative = states_dict.get("tentative", Decimal("0"))
        committed = states_dict.get("committed", Decimal("0"))
        actual = states_dict.get("actual", Decimal("0"))
        total = tentative + committed + actual
        non_billable = Decimal(str(member.non_billable_hours_percentage or 0))
        capacity_monthly = Decimal(str(member.billable_hours_per_week or 0)) * Decimal("4.33") * (Decimal("1") - non_billable)
        capacity_hours = capacity_monthly * Decimal(str(months_count))
        utilization_ratio = (total / capacity_hours) if capacity_hours > 0 else Decimal("0")
        members_response.append(
            CapacityMemberOverviewResponse(
                team_member_id=member.id,
                name=member.name,
                role=member.role,
                capacity_hours=capacity_hours,
                tentative_hours=tentative,
                committed_hours=committed,
                actual_hours=actual,
                total_hours=total,
                utilization_ratio=utilization_ratio,
            )
        )

    cell_hours_result = await db.execute(
        select(
            CapacityCommitment.cell_id,
            TeamCell.name,
            CapacityCommitment.state,
            func.sum(CapacityCommitment.hours).label("hours_sum"),
        )
        .join(TeamCell, TeamCell.id == CapacityCommitment.cell_id)
        .where(
            CapacityCommitment.organization_id == tenant.organization_id,
            CapacityCommitment.cell_id.isnot(None),
            CapacityCommitment.state.in_(normalized_states),
            CapacityCommitment.period_start <= period_end_dt,
            CapacityCommitment.period_end >= period_start_dt,
        )
        .group_by(CapacityCommitment.cell_id, TeamCell.name, CapacityCommitment.state)
    )
    cell_rows = cell_hours_result.all()
    cell_state_hours: dict[int, dict[str, Decimal]] = {}
    cell_names: dict[int, str] = {}
    for cell_id, cell_name, state_name, hours_sum in cell_rows:
        if cell_id is None:
            continue
        cell_names[cell_id] = cell_name or f"Cell {cell_id}"
        cell_state_hours.setdefault(cell_id, {})[state_name] = Decimal(str(hours_sum or 0))

    cells_response: list[CapacityCellOverviewResponse] = []
    for cell_id, states_dict in cell_state_hours.items():
        tentative = states_dict.get("tentative", Decimal("0"))
        committed = states_dict.get("committed", Decimal("0"))
        actual = states_dict.get("actual", Decimal("0"))
        total = tentative + committed + actual
        cells_response.append(
            CapacityCellOverviewResponse(
                cell_id=cell_id,
                cell_name=cell_names.get(cell_id, f"Cell {cell_id}"),
                tentative_hours=tentative,
                committed_hours=committed,
                actual_hours=actual,
                total_hours=total,
            )
        )

    totals = CapacityTotalsResponse(
        tentative_hours=sum((m.tentative_hours for m in members_response), start=Decimal("0")),
        committed_hours=sum((m.committed_hours for m in members_response), start=Decimal("0")),
        actual_hours=sum((m.actual_hours for m in members_response), start=Decimal("0")),
        total_hours=sum((m.total_hours for m in members_response), start=Decimal("0")),
    )

    logger.info(
        "Capacity overview generated",
        organization_id=tenant.organization_id,
        user_id=current_user.id,
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        states=normalized_states,
        members_count=len(members_response),
        cells_count=len(cells_response),
    )

    return CapacityOverviewResponse(
        period_start=period_start_dt,
        period_end=period_end_dt,
        months_count=months_count,
        states=normalized_states,
        members=members_response,
        cells=cells_response,
        totals=totals,
    )


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
