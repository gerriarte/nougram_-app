"""
Organization management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user, get_password_hash, create_access_token
from app.core.tenant import get_tenant_context, TenantContext
from app.core.exceptions import ResourceNotFoundError
from app.core.permissions import check_permission, PERM_INVITE_USERS, PERM_MANAGE_SUBSCRIPTION, PermissionError, get_user_role
from app.core.permission_middleware import require_invite_users, require_manage_subscription, require_super_admin
from app.core.logging import get_logger
from app.models.user import User
from app.models.organization import Organization
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListResponse,
    OrganizationRegisterRequest,
    OrganizationInviteRequest,
    OrganizationInviteResponse,
    OrganizationUserResponse,
    OrganizationUsersListResponse,
    OrganizationUsageStatsResponse,
    AddUserToOrganizationRequest,
    UpdateUserRoleRequest,
    UpdateSubscriptionPlanRequest,
    OnboardingConfigRequest,
    OnboardingConfigResponse
)

logger = get_logger(__name__)
router = APIRouter()


def require_super_admin_or_org_admin(
    current_user: User,
    organization_id: Optional[int] = None
) -> bool:
    """Check if user is super_admin or admin of the organization"""
    if getattr(current_user, 'role', None) == 'super_admin':
        return True
    
    if organization_id and current_user.organization_id == organization_id:
        # Check if user is org_admin (could be stored in settings or role)
        user_role = getattr(current_user, 'role', None)
        if user_role in ['org_admin', 'admin_financiero']:
            return True
    
    return False


@router.get("/me", response_model=OrganizationResponse, summary="Get my organization")
async def get_my_organization(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current authenticated user's organization.
    
    Returns organization details including:
    - Basic information (name, slug)
    - Subscription details (plan, status)
    - User count
    - Settings
    
    **Permissions:**
    - All authenticated users can access their own organization
    
    **Returns:**
    - `200 OK`: Organization found and returned
    - `404 Not Found`: User has no associated organization
    """
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not associated with any organization"
        )
    
    org_repo = OrganizationRepository(db)
    org = await org_repo.get_with_user_count(current_user.organization_id)
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        subscription_plan=org.subscription_plan,
        subscription_status=org.subscription_status,
        settings=org.settings,
        created_at=org.created_at,
        updated_at=org.updated_at,
        user_count=getattr(org, 'user_count', None)
    )


@router.get("/", response_model=OrganizationListResponse, summary="List organizations")
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    include_inactive: bool = Query(False, description="Include inactive organizations")
):
    """
    List organizations with pagination.
    
    **Permissions:**
    - **Super Admin**: Can see all organizations (active and inactive if `include_inactive=true`)
    - **Regular Users**: Can only see their own organization
    
    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `page_size`: Items per page (default: 20, max: 100)
    - `include_inactive`: Include organizations with inactive subscription status (default: false)
    
    **Returns:**
    - `200 OK`: List of organizations with pagination metadata
    
    **Example Response:**
    ```json
    {
      "items": [
        {
          "id": 1,
          "name": "My Organization",
          "slug": "my-org",
          "subscription_plan": "professional",
          "subscription_status": "active",
          "user_count": 5
        }
      ],
      "total": 1,
      "page": 1,
      "page_size": 20,
      "total_pages": 1
    }
    ```
    """
    org_repo = OrganizationRepository(db)
    
    # Check if user is super_admin
    is_super_admin = getattr(current_user, 'role', None) == 'super_admin'
    
    if is_super_admin:
        # Super admin can see all organizations
        organizations, total = await org_repo.list_all(
            page=page,
            page_size=page_size,
            include_inactive=include_inactive
        )
    else:
        # Regular users can only see their own organization
        if not current_user.organization_id:
            return OrganizationListResponse(
                items=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0
            )
        
        org = await org_repo.get_with_user_count(current_user.organization_id)
        if org:
            organizations = [org]
            total = 1
        else:
            organizations = []
            total = 0
    
    items = [
        OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            subscription_plan=org.subscription_plan,
            subscription_status=org.subscription_status,
            settings=org.settings,
            created_at=org.created_at,
            updated_at=org.updated_at,
            user_count=getattr(org, 'user_count', None)
        )
        for org in organizations
    ]
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return OrganizationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{organization_id}", response_model=OrganizationResponse, summary="Get organization by ID")
async def get_organization(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get organization details by ID.
    
    **Permissions:**
    - **Super Admin**: Can access any organization
    - **Regular Users**: Can only access their own organization
    
    **Returns:**
    - `200 OK`: Organization details
    - `404 Not Found`: Organization not found
    - `403 Forbidden`: User doesn't have permission to access this organization
    """
    org_repo = OrganizationRepository(db)
    org = await org_repo.get_with_user_count(organization_id)
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check permissions
    is_super_admin = getattr(current_user, 'role', None) == 'super_admin'
    if not is_super_admin and current_user.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this organization"
        )
    
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        subscription_plan=org.subscription_plan,
        subscription_status=org.subscription_status,
        settings=org.settings,
        created_at=org.created_at,
        updated_at=org.updated_at,
        user_count=getattr(org, 'user_count', None)
    )


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED, summary="Create organization")
async def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new organization (Admin only).
    
    **Permissions:**
    - **Super Admin**: Allowed
    - **All other users**: Forbidden (use `/organizations/register` for public registration)
    
    **Request Body:**
    - `name`: Organization name (required)
    - `slug`: URL-friendly identifier (optional, auto-generated from name if not provided)
    - `subscription_plan`: Initial plan (default: "free")
    - `subscription_status`: Initial status (default: "active")
    - `settings`: Optional JSON settings object
    
    **Returns:**
    - `201 Created`: Organization created successfully
    - `400 Bad Request`: Slug already exists or validation error
    - `403 Forbidden`: User doesn't have permission
    
    **Note:** For public registration, use `POST /organizations/register` instead.
    """
    # Check if user is super_admin
    is_super_admin = getattr(current_user, 'role', None) == 'super_admin'
    if not is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can create organizations. Use /organizations/register for public registration."
        )
    
    org_repo = OrganizationRepository(db)
    
    # Check if slug already exists
    if org_data.slug:
        existing = await org_repo.get_by_slug(org_data.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization with slug '{org_data.slug}' already exists"
            )
    
    # Create organization
    org = Organization(
        name=org_data.name,
        slug=org_data.slug or org_data.name.lower().replace(' ', '-'),
        subscription_plan=org_data.subscription_plan,
        subscription_status=org_data.subscription_status,
        settings=org_data.settings
    )
    
    db.add(org)
    await db.commit()
    await db.refresh(org)
    
    logger.info(f"Organization created: {org.id} ({org.name}) by user {current_user.id}")
    
    # Grant initial subscription credits
    try:
        from app.services.credit_service import CreditService
        await CreditService.grant_subscription_credits(org.id, db)
        logger.info(f"Granted initial subscription credits to organization {org.id} for plan {org.subscription_plan}")
    except Exception as e:
        # Log error but don't fail organization creation
        logger.error(f"Error granting initial subscription credits to organization {org.id}: {e}", exc_info=True)
    
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        subscription_plan=org.subscription_plan,
        subscription_status=org.subscription_status,
        settings=org.settings,
        created_at=org.created_at,
        updated_at=org.updated_at,
        user_count=0
    )


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED, summary="Register new organization (Public)")
async def register_organization(
    registration_data: OrganizationRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint to register a new organization.
    
    This endpoint is **public** (no authentication required) and creates:
    1. A new organization
    2. An admin user for that organization
    3. Returns organization details and access token for immediate login
    
    **Request Body:**
    - `organization_name`: Organization name (required)
    - `organization_slug`: URL-friendly identifier (optional)
    - `admin_email`: Admin user email (required)
    - `admin_full_name`: Admin user full name (required)
    - `admin_password`: Admin user password, min 8 characters (required)
    - `subscription_plan`: Initial plan (default: "free")
    
    **Returns:**
    - `201 Created`: Organization and admin user created
    - `400 Bad Request`: Slug already exists, email already registered, or validation error
    
    **Response includes:**
    - `organization`: Created organization object
    - `user`: Created admin user object
    - `access_token`: JWT token for immediate authentication
    - `token_type`: "bearer"
    
    **Example Request:**
    ```json
    {
      "organization_name": "My New Agency",
      "organization_slug": "my-new-agency",
      "admin_email": "admin@agency.com",
      "admin_full_name": "John Doe",
      "admin_password": "securepassword123",
      "subscription_plan": "free"
    }
    ```
    """
    org_repo = OrganizationRepository(db)
    
    # Check if slug already exists
    slug = registration_data.organization_slug
    if not slug:
        # Generate slug from name
        import re
        slug = re.sub(r'[^\w\s-]', '', registration_data.organization_name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug[:50]
    
    existing = await org_repo.get_by_slug(slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization with slug '{slug}' already exists. Please choose a different name."
        )
    
    # Check if email already exists
    existing_user = await db.execute(
        select(User).where(User.email == registration_data.admin_email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )
    
    # Create organization
    org = Organization(
        name=registration_data.organization_name,
        slug=slug,
        subscription_plan=registration_data.subscription_plan,
        subscription_status="active",
        settings={}
    )
    
    db.add(org)
    await db.commit()
    await db.refresh(org)
    
    # Create admin user - always as "owner" role
    from app.core.permissions import get_role_type
    admin_user = User(
        email=registration_data.admin_email,
        full_name=registration_data.admin_full_name,
        hashed_password=get_password_hash(registration_data.admin_password),
        organization_id=org.id,
        role="owner",  # Always create as owner
        role_type="tenant"  # Tenant role type
    )
    
    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)
    
    # Generate access token
    token_data = {
        "sub": str(admin_user.id),
        "email": admin_user.email,
        "name": admin_user.full_name,
        "organization_id": org.id
    }
    access_token = create_access_token(token_data)
    
    logger.info(f"Organization registered: {org.id} ({org.name}) with admin user {admin_user.id}")
    
    # Grant initial subscription credits
    try:
        from app.services.credit_service import CreditService
        await CreditService.grant_subscription_credits(org.id, db)
        logger.info(f"Granted initial subscription credits to organization {org.id} for plan {org.subscription_plan}")
    except Exception as e:
        # Log error but don't fail organization registration
        logger.error(f"Error granting initial subscription credits to organization {org.id}: {e}", exc_info=True)
    
    return {
        "organization": OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            subscription_plan=org.subscription_plan,
            subscription_status=org.subscription_status,
            settings=org.settings,
            created_at=org.created_at,
            updated_at=org.updated_at,
            user_count=1
        ),
        "user": {
            "id": admin_user.id,
            "email": admin_user.email,
            "full_name": admin_user.full_name,
            "role": admin_user.role
        },
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: int,
    org_data: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an organization
    
    - Super admin: can update any organization
    - Org admin: can update their own organization
    """
    org_repo = OrganizationRepository(db)
    org = await org_repo.get_by_id(organization_id)
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check permissions
    is_super_admin = getattr(current_user, 'role', None) == 'super_admin'
    is_org_admin = (
        current_user.organization_id == organization_id and
        getattr(current_user, 'role', None) in ['org_admin', 'admin_financiero', 'owner']
    )
    
    if not (is_super_admin or is_org_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this organization"
        )
    
    # Update fields
    if org_data.name is not None:
        org.name = org_data.name
    if org_data.slug is not None:
        # Check if new slug is available
        existing = await org_repo.get_by_slug(org_data.slug)
        if existing and existing.id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization with slug '{org_data.slug}' already exists"
            )
        org.slug = org_data.slug
    if org_data.subscription_plan is not None and is_super_admin:
        org.subscription_plan = org_data.subscription_plan
    if org_data.subscription_status is not None and is_super_admin:
        org.subscription_status = org_data.subscription_status
    if org_data.settings is not None:
        if org.settings is None:
            org.settings = {}
        org.settings.update(org_data.settings)
    
    await db.commit()
    await db.refresh(org)
    
    logger.info(f"Organization updated: {org.id} by user {current_user.id}")
    
    user_count = await org_repo.get_user_count(organization_id)
    
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        subscription_plan=org.subscription_plan,
        subscription_status=org.subscription_status,
        settings=org.settings,
        created_at=org.created_at,
        updated_at=org.updated_at,
        user_count=user_count
    )


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete an organization (only super_admin)
    
    Note: This is a soft delete - the organization is marked as cancelled
    but data is preserved for compliance/audit purposes
    """
    # Only super_admin can delete organizations
    is_super_admin = getattr(current_user, 'role', None) == 'super_admin'
    if not is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can delete organizations"
        )
    
    org_repo = OrganizationRepository(db)
    org = await org_repo.get_by_id(organization_id)
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Soft delete: mark as cancelled
    org.subscription_status = "cancelled"
    await db.commit()
    
    logger.info(f"Organization soft deleted: {org.id} by user {current_user.id}")
    
    return None


@router.get("/{organization_id}/users", response_model=OrganizationUsersListResponse)
async def list_organization_users(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List users in an organization
    
    - Super admin: can see users of any organization
    - Org admin: can see users of their own organization
    """
    # Check permissions
    is_super_admin = getattr(current_user, 'role', None) == 'super_admin'
    is_org_admin = (
        current_user.organization_id == organization_id and
        getattr(current_user, 'role', None) in ['org_admin', 'admin_financiero']
    )
    
    if not (is_super_admin or is_org_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view users of this organization"
        )
    
    org_repo = OrganizationRepository(db)
    users = await org_repo.get_users(organization_id)
    
    items = [
        OrganizationUserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            organization_id=user.organization_id,
            created_at=getattr(user, 'created_at', None)  # Handle missing created_at field
        )
        for user in users
    ]
    
    return OrganizationUsersListResponse(items=items, total=len(items))


@router.post("/{organization_id}/invite", response_model=OrganizationInviteResponse, deprecated=True)
async def invite_user_to_organization(
    organization_id: int,
    invite_data: OrganizationInviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Invite a user to join an organization (DEPRECATED - Use POST /organizations/{id}/invitations instead)
    
    This endpoint is kept for backward compatibility but now uses the new invitation system.
    It creates an invitation in the database and sends an email.
    
    **Permissions:**
    - Requires `can_invite_users` permission
    - Super admin: can invite to any organization
    - Owner: can invite to their own organization
    """
    from datetime import datetime, timezone, timedelta
    import secrets
    from app.repositories.invitation_repository import InvitationRepository
    from app.schemas.invitation import InvitationCreate
    from app.api.v1.endpoints.invitations import _generate_invitation_token, _get_invitation_expiry_days, _send_invitation_email
    
    # Check permissions
    try:
        check_permission(current_user, PERM_INVITE_USERS)
    except PermissionError:
        return OrganizationInviteResponse(
            success=False,
            message="You don't have permission to invite users",
            invitation_token=None
        )
    
    # Additional check: non-super_admin users can only invite to their own organization
    user_role = get_user_role(current_user)
    is_super_admin = user_role == 'super_admin'
    is_owner = (
        user_role == 'owner' and
        current_user.organization_id == organization_id
    )
    
    if not (is_super_admin or is_owner):
        return OrganizationInviteResponse(
            success=False,
            message="You can only invite users to your own organization",
            invitation_token=None
        )
    
    # Verify organization exists
    org_repo = OrganizationRepository(db)
    org = await org_repo.get_by_id(organization_id)
    if not org:
        return OrganizationInviteResponse(
            success=False,
            message="Organization not found",
            invitation_token=None
        )
    
    # Check if user already exists and is in organization
    existing_user = await db.execute(
        select(User).where(User.email == invite_data.email)
    )
    user = existing_user.scalar_one_or_none()
    
    if user and user.organization_id == organization_id:
        return OrganizationInviteResponse(
            success=False,
            message=f"User {invite_data.email} is already a member of this organization",
            invitation_token=None
        )
    
    # Check for existing pending invitation
    invitation_repo = InvitationRepository(db, tenant_id=organization_id)
    existing_invitation = await invitation_repo.get_by_email_and_org(
        invite_data.email,
        organization_id
    )
    
    if existing_invitation and not existing_invitation.is_expired:
        return OrganizationInviteResponse(
            success=False,
            message=f"A pending invitation already exists for {invite_data.email}",
            invitation_token=None
        )
    
    # Generate token and expiration
    token = _generate_invitation_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=_get_invitation_expiry_days())
    
    # Create invitation
    invitation = await invitation_repo.create_invitation(
        organization_id=organization_id,
        email=invite_data.email,
        role=invite_data.role,
        token=token,
        expires_at=expires_at,
        created_by_id=current_user.id
    )
    
    await db.commit()
    await db.refresh(invitation)
    
    # Send invitation email
    email_sent = await _send_invitation_email(invitation, org)
    if not email_sent:
        logger.warning(
            f"Failed to send invitation email to {invite_data.email}",
            invitation_id=invitation.id,
            organization_id=organization_id
        )
    
    logger.info(
        f"Invitation created for {invite_data.email} to organization {organization_id}",
        invitation_id=invitation.id,
        created_by=current_user.id
    )
    
    return OrganizationInviteResponse(
        success=True,
        message=f"Invitation sent to {invite_data.email}",
        invitation_token=token  # Include token for backward compatibility
    )


@router.get("/{organization_id}/stats", response_model=OrganizationUsageStatsResponse, summary="Get organization usage statistics")
async def get_organization_usage_stats(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get usage statistics for an organization.
    
    Returns current usage counts and plan limits for:
    - Users
    - Projects
    - Services
    - Team Members
    
    Also includes usage percentages (0-100%) for each resource type.
    
    **Permissions:**
    - **Super Admin**: Can view stats for any organization
    - **Org Admin**: Can view stats for their own organization
    
    **Returns:**
    - `200 OK`: Usage statistics with current usage, limits, and percentages
    - `403 Forbidden`: User doesn't have permission
    - `404 Not Found`: Organization not found
    
    **Example Response:**
    ```json
    {
      "organization_id": 1,
      "organization_name": "My Organization",
      "subscription_plan": "professional",
      "current_usage": {
        "users": 15,
        "projects": 45,
        "services": 80,
        "team_members": 25
      },
      "limits": {
        "users": 20,
        "projects": 100,
        "services": 200,
        "team_members": 50
      },
      "usage_percentage": {
        "users": 75.0,
        "projects": 45.0,
        "services": 40.0,
        "team_members": 50.0
      }
    }
    ```
    """
    # Check permissions
    is_super_admin = getattr(current_user, 'role', None) == 'super_admin'
    is_org_admin = (
        current_user.organization_id == organization_id and
        getattr(current_user, 'role', None) in ['org_admin', 'admin_financiero']
    )
    
    if not (is_super_admin or is_org_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view usage statistics for this organization"
        )
    
    org_repo = OrganizationRepository(db)
    org = await org_repo.get_by_id(organization_id)
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Get current usage
    user_count = await org_repo.get_user_count(organization_id)
    project_count = await org_repo.get_project_count(organization_id)
    
    # Get service count
    from app.models.service import Service
    service_count_result = await db.execute(
        select(func.count(Service.id)).where(
            Service.organization_id == organization_id,
            Service.deleted_at.is_(None)
        )
    )
    service_count = service_count_result.scalar() or 0
    
    # Get team member count
    from app.models.team import TeamMember
    team_count_result = await db.execute(
        select(func.count(TeamMember.id)).where(
            TeamMember.organization_id == organization_id
        )
    )
    team_count = team_count_result.scalar() or 0
    
    # Get limits from plan
    from app.core.plan_limits import get_plan_limit
    limits = {
        "users": get_plan_limit(org.subscription_plan, "max_users"),
        "projects": get_plan_limit(org.subscription_plan, "max_projects"),
        "services": get_plan_limit(org.subscription_plan, "max_services"),
        "team_members": get_plan_limit(org.subscription_plan, "max_team_members"),
    }
    
    # Calculate usage percentage
    def calc_percentage(current: int, limit: int) -> float:
        if limit == -1:  # Unlimited
            return 0.0
        if limit == 0:
            return 100.0
        return min(100.0, (current / limit) * 100.0)
    
    usage_percentage = {
        "users": calc_percentage(user_count, limits["users"]),
        "projects": calc_percentage(project_count, limits["projects"]),
        "services": calc_percentage(service_count, limits["services"]),
        "team_members": calc_percentage(team_count, limits["team_members"]),
    }
    
    return OrganizationUsageStatsResponse(
        organization_id=org.id,
        organization_name=org.name,
        subscription_plan=org.subscription_plan,
        current_usage={
            "users": user_count,
            "projects": project_count,
            "services": service_count,
            "team_members": team_count,
        },
        limits=limits,
        usage_percentage=usage_percentage
    )


@router.post("/{organization_id}/users", response_model=OrganizationUserResponse, status_code=status.HTTP_201_CREATED)
async def add_user_to_organization(
    organization_id: int,
    user_data: AddUserToOrganizationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a user to an organization
    
    **Permissions:**
    - Requires `can_invite_users` permission
    - Super admin: can add users to any organization
    - Owner: can add users to their own organization
    - Denied roles: admin_financiero, product_manager, collaborator
    
    Can either:
    1. Add existing user by user_id
    2. Create new user by email (requires full_name and password)
    """
    # Check permissions
    try:
        check_permission(current_user, PERM_INVITE_USERS)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to add users"
        )
    
    # Additional check: non-super_admin users can only add users to their own organization
    from app.core.roles import SUPPORT_ROLES, TENANT_ROLES
    from app.core.permissions import validate_super_admin_email
    
    user_role = get_user_role(current_user)
    is_super_admin = user_role == 'super_admin'
    is_owner = (
        user_role == 'owner' and
        current_user.organization_id == organization_id
    )
    
    if not (is_super_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add users to your own organization"
        )
    
    # Validate role assignment
    requested_role = user_data.role
    if requested_role in SUPPORT_ROLES:
        # Only super_admin can add support roles
        if not is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super_admin can add users with support roles"
            )
        # Validate super_admin email if assigning super_admin role
        if requested_role == 'super_admin':
            email_to_check = user_data.email if user_data.email else None
            if email_to_check:
                validate_super_admin_email(email_to_check, requested_role)
    elif requested_role in TENANT_ROLES:
        # Owner can add tenant roles, but not owner (only registration creates owner)
        if requested_role == 'owner':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign owner role. Only registration creates owner users."
            )
        # Owner can only add users to their own organization
        if is_owner and current_user.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only add users to your own organization"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {requested_role}"
        )
    
    # Verify organization exists and validate limits
    org_repo = OrganizationRepository(db)
    org = await org_repo.get_by_id(organization_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Validate user limit
    from app.core.plan_limits import validate_user_limit
    await validate_user_limit(organization_id, org.subscription_plan, db)
    
    user = None
    
    if user_data.user_id:
        # Add existing user
        existing_user = await db.execute(
            select(User).where(User.id == user_data.user_id)
        )
        user = existing_user.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.organization_id and user.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User already belongs to another organization"
            )
        
        # Update user organization and role
        user.organization_id = organization_id
        user.role = user_data.role
        await db.commit()
        await db.refresh(user)
        
    elif user_data.email:
        # Create new user
        if not user_data.full_name or not user_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="full_name and password are required when creating a new user"
            )
        
        # Check if email already exists
        existing_user = await db.execute(
            select(User).where(User.email == user_data.email.lower().strip())
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists"
            )
        
        # Create new user
        user = User(
            email=user_data.email.lower().strip(),
            full_name=user_data.full_name,
            hashed_password=get_password_hash(user_data.password),
            organization_id=organization_id,
            role=user_data.role
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either user_id or email must be provided"
        )
    
    logger.info(f"User {user.id} added to organization {organization_id} by user {current_user.id}")
    
    return OrganizationUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization_id=user.organization_id,
        created_at=getattr(user, 'created_at', None)
    )


@router.put("/{organization_id}/users/{user_id}/role", response_model=OrganizationUserResponse)
async def update_user_role_in_organization(
    organization_id: int,
    user_id: int,
    role_data: UpdateUserRoleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user role in an organization
    
    **Permissions:**
    - Super admin: can assign support roles (super_admin, support_manager, data_analyst)
    - Owner: can assign tenant roles (admin_financiero, product_manager, collaborator) in their organization
    """
    from app.core.roles import SUPPORT_ROLES, TENANT_ROLES
    from app.core.permissions import validate_super_admin_email, get_user_role
    
    current_role = get_user_role(current_user)
    is_super_admin = current_role == 'super_admin'
    is_owner = (
        current_role == 'owner' and
        current_user.organization_id == organization_id
    )
    
    # Validate role assignment permissions
    new_role = role_data.role
    
    # Check if trying to assign support role
    if new_role in SUPPORT_ROLES:
        if not is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super_admin can assign support roles"
            )
        # Validate super_admin email
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        target_user = user_result.scalar_one_or_none()
        if target_user:
            validate_super_admin_email(target_user.email, new_role)
    
    # Check if trying to assign tenant role
    elif new_role in TENANT_ROLES:
        if not (is_super_admin or is_owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner or super_admin can assign tenant roles"
            )
        # Owner can only assign roles in their own organization
        if is_owner and current_user.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only assign roles in your own organization"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {new_role}"
        )
    
    # Verify organization exists
    org_repo = OrganizationRepository(db)
    org = await org_repo.get_by_id(organization_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Get user
    user_result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.organization_id == organization_id
        )
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in this organization"
        )
    
    # Additional validations
    current_user_role = get_user_role(user)
    
    # Prevent owner from changing their own role
    if is_owner and user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot change your own role"
        )
    
    # Only super_admin can change owner role to another role
    if current_user_role == 'owner' and new_role != 'owner':
        if not is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super_admin can change owner role"
            )
    
    # Prevent removing last owner (only super_admin can do this)
    if new_role != "owner" and current_user_role == "owner":
        # Check if there are other owners
        owner_count_result = await db.execute(
            select(func.count(User.id)).where(
                User.organization_id == organization_id,
                User.role == "owner"
            )
        )
        owner_count = owner_count_result.scalar() or 0
        
        if owner_count <= 1 and not is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner. Only super_admin can change owner role."
            )
    
    # Update role and role_type
    user.role = new_role
    from app.core.roles import get_role_type
    user.role_type = get_role_type(new_role)
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"User {user.id} role updated to {role_data.role} in organization {organization_id} by user {current_user.id}")
    
    return OrganizationUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization_id=user.organization_id,
        created_at=getattr(user, 'created_at', None)
    )


@router.delete("/{organization_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_from_organization(
    organization_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a user from an organization
    
    - Super admin: can remove users from any organization
    - Org admin: can remove users from their own organization
    
    Note: This does not delete the user, only removes them from the organization
    """
    # Check permissions
    is_super_admin = getattr(current_user, 'role', None) == 'super_admin'
    is_org_admin = (
        current_user.organization_id == organization_id and
        getattr(current_user, 'role', None) in ['org_admin', 'admin_financiero']
    )
    
    if not (is_super_admin or is_org_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to remove users from this organization"
        )
    
    # Prevent self-removal
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove yourself from the organization"
        )
    
    # Verify organization exists
    org_repo = OrganizationRepository(db)
    org = await org_repo.get_by_id(organization_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Get user
    user_result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.organization_id == organization_id
        )
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in this organization"
        )
    
    # Prevent removing last org_admin
    if user.role == "org_admin":
        admin_count_result = await db.execute(
            select(func.count(User.id)).where(
                User.organization_id == organization_id,
                User.role == "org_admin"
            )
        )
        admin_count = admin_count_result.scalar() or 0
        
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last organization admin. Please assign another admin first."
            )
    
    # Remove user from organization (set organization_id to None)
    user.organization_id = None
    await db.commit()
    
    logger.info(f"User {user_id} removed from organization {organization_id} by user {current_user.id}")
    
    return None


@router.put("/{organization_id}/subscription", response_model=OrganizationResponse)
async def update_subscription_plan(
    organization_id: int,
    subscription_data: UpdateSubscriptionPlanRequest,
    current_user: User = Depends(get_current_user),  # Permission check inside due to multi-tenant logic
    db: AsyncSession = Depends(get_db)
):
    """
    Update organization subscription plan
    
    **Permissions:**
    - Requires `can_manage_subscription` permission
    - Super admin: can update any organization's subscription
    - Owner: can update their own organization's subscription
    - Denied roles: admin_financiero, product_manager, collaborator
    """
    # Check permissions
    try:
        check_permission(current_user, PERM_MANAGE_SUBSCRIPTION)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage subscriptions"
        )
    
    # Additional check: non-super_admin users can only update their own organization's subscription
    user_role = get_user_role(current_user)
    is_super_admin = user_role == 'super_admin'
    is_owner = (
        user_role == 'owner' and
        current_user.organization_id == organization_id
    )
    
    if not (is_super_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own organization's subscription"
        )
    
    org_repo = OrganizationRepository(db)
    org = await org_repo.update_subscription(
        organization_id,
        plan=subscription_data.plan,
        status=subscription_data.status
    )
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    user_count = await org_repo.get_user_count(organization_id)
    
    logger.info(f"Subscription updated for organization {organization_id} to {subscription_data.plan} by user {current_user.id}")
    
    # Grant subscription credits when plan is updated
    if subscription_data.plan:
        try:
            from app.services.credit_service import CreditService
            await CreditService.grant_subscription_credits(organization_id, db)
            logger.info(f"Granted subscription credits to organization {organization_id} for updated plan {subscription_data.plan}")
        except Exception as e:
            # Log error but don't fail subscription update
            logger.error(f"Error granting subscription credits to organization {organization_id}: {e}", exc_info=True)
    
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        subscription_plan=org.subscription_plan,
        subscription_status=org.subscription_status,
        settings=org.settings,
        created_at=org.created_at,
        updated_at=org.updated_at,
        user_count=user_count
    )


@router.post("/{organization_id}/onboarding-config", response_model=OnboardingConfigResponse, summary="Save onboarding configuration")
async def save_onboarding_config(
    organization_id: int,
    config_data: OnboardingConfigRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Save onboarding configuration for an organization (Sprint 18).
    
    Stores configuration data in the organization's settings JSON field:
    - Social charges configuration (Ley 100 for Colombia)
    - Tax structure (IVA, ICA, retentions)
    - Country and currency
    - Profile type
    
    **Permissions:**
    - **Super Admin**: Can update any organization
    - **Owner/Admin**: Can update their own organization
    
    **Request Body:**
    - `social_charges_config`: Social charges configuration (optional)
    - `tax_structure`: Tax structure dictionary (optional)
    - `country`: Country code (optional)
    - `currency`: Currency code (optional)
    - `profile_type`: Profile type (optional)
    
    **Returns:**
    - `200 OK`: Configuration saved successfully
    - `404 Not Found`: Organization not found
    - `403 Forbidden`: User doesn't have permission
    """
    org_repo = OrganizationRepository(db)
    org = await org_repo.get_by_id(organization_id)
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check permissions
    is_super_admin = getattr(current_user, 'role', None) == 'super_admin'
    is_org_admin = (
        current_user.organization_id == organization_id and
        getattr(current_user, 'role', None) in ['owner', 'admin_financiero']
    )
    
    if not (is_super_admin or is_org_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this organization's configuration"
        )
    
    # Initialize settings if None
    if org.settings is None:
        org.settings = {}
    
    # Calculate total percentage for social charges if provided
    if config_data.social_charges_config:
        social_config = config_data.social_charges_config.model_dump(exclude_none=True)
        
        # Calculate total percentage if individual percentages are provided
        if 'health_percentage' in social_config or 'pension_percentage' in social_config or \
           'arl_percentage' in social_config or 'parafiscales_percentage' in social_config or \
           'prima_services_percentage' in social_config or 'cesantias_percentage' in social_config or \
           'int_cesantias_percentage' in social_config or 'vacations_percentage' in social_config:
            total = (
                social_config.get('health_percentage', 0) +
                social_config.get('pension_percentage', 0) +
                social_config.get('arl_percentage', 0) +
                social_config.get('parafiscales_percentage', 0) +
                social_config.get('prima_services_percentage', 0) +
                social_config.get('cesantias_percentage', 0) +
                social_config.get('int_cesantias_percentage', 0) +
                social_config.get('vacations_percentage', 0)
            )
            social_config['total_percentage'] = total
        
        org.settings['social_charges_config'] = social_config
    
    # Store other onboarding data
    if config_data.tax_structure is not None:
        org.settings['tax_structure'] = config_data.tax_structure
    
    if config_data.country is not None:
        org.settings['country'] = config_data.country
    
    if config_data.currency is not None:
        org.settings['currency'] = config_data.currency
    
    if config_data.profile_type is not None:
        org.settings['profile_type'] = config_data.profile_type
    
    await db.commit()
    await db.refresh(org)
    
    logger.info(f"Onboarding config saved for organization {organization_id} by user {current_user.id}")
    
    return OnboardingConfigResponse(
        success=True,
        message="Onboarding configuration saved successfully",
        organization_id=organization_id,
        settings=org.settings
    )


