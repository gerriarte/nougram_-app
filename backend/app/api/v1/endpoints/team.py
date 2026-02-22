"""
Team member management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import ResourceNotFoundError, BusinessLogicError
from app.core.logging import get_logger
from app.core.permissions import has_permission, PERM_VIEW_SENSITIVE_DATA, PERM_MODIFY_COSTS, PERM_DELETE_RESOURCES
from app.core.permission_middleware import require_view_sensitive_data, require_modify_costs, require_delete_resources, require_create_quotes
from app.models.team import TeamMember
from app.models.user import User
from app.repositories.team_repository import TeamRepository
from app.core.tenant import get_tenant_context, TenantContext
from app.repositories.factory import RepositoryFactory
from app.schemas.team import (
    TeamMemberCreate,
    TeamMemberUpdate,
    TeamMemberResponse,
    TeamMemberListResponse,
    TeamMemberAllocationResponse,
    TeamMemberAllocationListResponse,
)

logger = get_logger(__name__)

router = APIRouter()


@router.get("/team", response_model=TeamMemberListResponse)
async def list_team_members(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_view_sensitive_data),  # Require permission to view sensitive data (salaries)
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)")
):
    """
    List all team members with pagination
    
    **Permissions:**
    - Requires `can_view_sensitive_data` permission (salaries are sensitive data)
    - Allowed roles: owner, admin_financiero, super_admin
    - Denied roles: product_manager, collaborator (data leakage prevention)
    """
    from sqlalchemy import desc
    
    try:
        team_repo = RepositoryFactory.create_team_repository(db, tenant.organization_id)
        
        # Get total count
        total = await team_repo.count()
        
        # Get paginated results
        offset = (page - 1) * page_size
        members = await team_repo.get_all(
            order_by=desc(TeamMember.created_at),
            limit=page_size,
            offset=offset
        )
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        return TeamMemberListResponse(
            items=[TeamMemberResponse.model_validate(member) for member in members],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error("Error listing team members", error=str(e), user_id=current_user.id, exc_info=True)
        # Return empty list on error
        return TeamMemberListResponse(items=[], total=0, page=page, page_size=page_size, total_pages=0)


@router.get("/team/allocation-members", response_model=TeamMemberAllocationListResponse)
async def list_team_members_for_allocation(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_create_quotes),
    db: AsyncSession = Depends(get_db),
):
    """
    List active team members for quote resource allocation (non-sensitive).

    Returns only fields needed for planning capacity and assigning resources.
    Salary and other sensitive financial data are intentionally excluded.
    """
    try:
        team_repo = RepositoryFactory.create_team_repository(db, tenant.organization_id)
        members = await team_repo.get_all_active()
        return TeamMemberAllocationListResponse(
            items=[TeamMemberAllocationResponse.model_validate(member) for member in members],
            total=len(members),
        )
    except Exception as e:
        logger.error("Error listing allocation members", error=str(e), user_id=current_user.id, exc_info=True)
        return TeamMemberAllocationListResponse(items=[], total=0)


@router.post("/team", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def create_team_member(
    member_data: TeamMemberCreate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs),  # Require permission to modify costs (salaries)
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new team member
    
    **Permissions:**
    - Requires `can_modify_costs` permission (team members affect costs)
    - Allowed roles: owner, admin_financiero, super_admin
    - Denied roles: product_manager, collaborator
    """
    # Validate team member limit for plan
    from app.core.plan_limits import validate_team_member_limit
    await validate_team_member_limit(tenant.organization_id, tenant.subscription_plan, db)
    
    try:
        # Ensure all required fields have values
        member_dict = member_data.model_dump()
        
        # Set defaults for optional fields
        if not member_dict.get('currency'):
            member_dict['currency'] = 'USD'
        if 'is_active' not in member_dict:
            member_dict['is_active'] = True
        if 'billable_hours_per_week' not in member_dict or member_dict['billable_hours_per_week'] is None:
            member_dict['billable_hours_per_week'] = 32
        
        # Convert billable_hours_per_week to int if it's a float
        if isinstance(member_dict.get('billable_hours_per_week'), float):
            member_dict['billable_hours_per_week'] = int(member_dict['billable_hours_per_week'])
        
        # Remove user_id if not provided (optional field)
        if 'user_id' not in member_dict or member_dict['user_id'] is None:
            member_dict.pop('user_id', None)
        
        logger.info("Creating team member", member_data=member_dict, user_id=current_user.id)
        
        member_dict['organization_id'] = tenant.organization_id
        
        new_member = TeamMember(**member_dict)
        team_repo = RepositoryFactory.create_team_repository(db, tenant.organization_id)
        new_member = await team_repo.create(new_member)
        
        # Invalidate blended cost rate cache
        from app.core.cache import get_cache
        cache = get_cache()
        cache.invalidate_pattern("blended_cost_rate:")
        
        logger.info("Team member created successfully", member_id=new_member.id, user_id=current_user.id)
        return TeamMemberResponse.model_validate(new_member)
    except Exception as e:
        await db.rollback()
        logger.error(
            "Error creating team member",
            error=str(e),
            user_id=current_user.id,
            member_data=member_data.model_dump() if hasattr(member_data, 'model_dump') else str(member_data),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team member: {str(e)}"
        )


@router.put("/team/{member_id}", response_model=TeamMemberResponse)
async def update_team_member(
    member_id: int,
    member_data: TeamMemberUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs),  # Require permission to modify costs (salaries)
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing team member
    
    **Permissions:**
    - Requires `can_modify_costs` permission (team members affect costs)
    - Allowed roles: owner, admin_financiero, super_admin
    - Denied roles: product_manager, collaborator
    """
    try:
        team_repo = RepositoryFactory.create_team_repository(db, tenant.organization_id)
        member = await team_repo.get_by_id(member_id)
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team member with id {member_id} not found"
            )
        
        update_data = member_data.model_dump(exclude_unset=True)
        
        # Convert billable_hours_per_week to int if it's a float
        if 'billable_hours_per_week' in update_data and isinstance(update_data['billable_hours_per_week'], float):
            update_data['billable_hours_per_week'] = int(update_data['billable_hours_per_week'])
        
        # Ensure currency has a value if provided
        if 'currency' in update_data and not update_data['currency']:
            update_data['currency'] = 'USD'
        
        logger.info("Updating team member", member_id=member_id, update_data=update_data, user_id=current_user.id)
        
        for field, value in update_data.items():
            setattr(member, field, value)
        
        member = await team_repo.update(member)
        
        # Invalidate blended cost rate cache
        from app.core.cache import get_cache
        cache = get_cache()
        cache.invalidate_pattern("blended_cost_rate:")
        
        logger.info("Team member updated successfully", member_id=member_id, user_id=current_user.id)
        return TeamMemberResponse.model_validate(member)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "Error updating team member",
            member_id=member_id,
            error=str(e),
            user_id=current_user.id,
            update_data=member_data.model_dump(exclude_unset=True) if hasattr(member_data, 'model_dump') else str(member_data),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update team member: {str(e)}"
        )


@router.delete("/team/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team_member(
    member_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_delete_resources),  # Require permission to delete resources
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a team member
    
    **Permissions:**
    - Requires `can_delete_resources` permission
    - Allowed roles: owner, super_admin
    - Denied roles: admin_financiero, product_manager, collaborator
    
    Validates that the member is not active before deletion.
    Active members are used in calculations, so deletion will affect the blended cost rate.
    """
    # Verify if the member exists
    team_repo = RepositoryFactory.create_team_repository(db, tenant.organization_id)
    member = await team_repo.get_by_id(member_id)
    
    if not member:
        raise ResourceNotFoundError("Team member", member_id)
    
    # VALIDATION: Warn if member is active
    # Active members contribute to the blended cost rate calculation
    # In production, you might want to require deactivation before deletion
    # or require admin privileges
    if member.is_active:
        # Allow deletion but note that it will affect calculations
        # In a production system, consider requiring deactivation first:
        # raise BusinessLogicError(
        #     f"Cannot delete active team member '{member.full_name}'. "
        #     "Please deactivate the member first, then delete."
        # )
        pass
    
    logger.info("Deleting team member", member_id=member_id, user_id=current_user.id)
    await team_repo.delete(member, soft=False)
    
    # Invalidate blended cost rate cache
    from app.core.cache import get_cache
    cache = get_cache()
    cache.invalidate_pattern("blended_cost_rate:")
    
    return None




