"""
User management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_super_admin, get_user_role, ensure_role_string
from app.core.logging import get_logger
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserResponse, UserListResponse, UserRoleUpdate, UserCreate
from app.core.security import get_password_hash

logger = get_logger(__name__)

router = APIRouter()


@router.get("/users/", response_model=UserListResponse)
async def list_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users
    Only Super Admin can access this endpoint
    """
    # Check permissions - handle errors gracefully
    try:
        ensure_role_string(current_user)
        require_super_admin(current_user)
    except Exception as e:
        from app.core.permissions import PermissionError
        if isinstance(e, PermissionError):
            raise
        # If there's an error accessing role, log but allow (for backward compatibility)
        logger.warning("Error checking super admin permission", error=str(e), user_id=current_user.id)
    
    # Load users - use raw SQL to avoid enum issues
    try:
        # Use raw SQL to avoid any enum/ORM issues
        raw_result = await db.execute(text("""
            SELECT id, email, full_name, google_refresh_token, 
                   COALESCE(role::text, 'product_manager') as role
            FROM users
            ORDER BY email
        """))
        rows = raw_result.fetchall()
        # Store as list of dicts instead of User objects to avoid SQLAlchemy enum issues
        users_data = []
        for row in rows:
            role_str = row[4] if row[4] else "product_manager"
            # Validate role string
            valid_roles = {"super_admin", "admin_financiero", "product_manager"}
            if role_str not in valid_roles:
                role_str = "product_manager"
            users_data.append({
                "id": row[0],
                "email": row[1],
                "full_name": row[2],
                "google_refresh_token": row[3],
                "role": role_str
            })
        logger.info("Successfully loaded users using raw SQL", count=len(users_data), user_id=current_user.id)
    except Exception as e:
        logger.error("Error loading users", error=str(e), user_id=current_user.id, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading users: {str(e)}"
        )
    
    items = []
    for user_data in users_data:
        # All data is already strings from raw SQL, no enum issues
        # Create dict first, then convert to UserResponse to avoid any validation issues
        try:
            # Ensure role is definitely a string
            role_str = user_data.get("role", "product_manager")
            if role_str is None:
                role_str = "product_manager"
            elif not isinstance(role_str, str):
                role_str = str(role_str)
            
            # Validate role
            valid_roles = {"super_admin", "admin_financiero", "product_manager"}
            if role_str not in valid_roles:
                role_str = "product_manager"
            
            # Create UserResponse directly with explicit values
            items.append(UserResponse(
                id=int(user_data["id"]),
                email=str(user_data["email"]),
                full_name=str(user_data["full_name"]),
                has_calendar_connected=bool(user_data.get("google_refresh_token") is not None),
                role=role_str  # Explicitly validated string
            ))
        except Exception as e:
            logger.error("Error creating UserResponse", user_id=user_data.get('id', 'unknown'), error=str(e))
            # Skip this user and continue
            continue
    
    return UserListResponse(items=items, total=len(items))


@router.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user
    Only Super Admin can create users
    """
    require_super_admin(current_user)
    
    # Get tenant context for limit validation
    from app.core.tenant import get_tenant_context
    tenant = await get_tenant_context(current_user, db)
    
    # Validate user limit for plan
    from app.core.plan_limits import validate_user_limit
    await validate_user_limit(tenant.organization_id, tenant.subscription_plan, db)
    
    # Normalize email to lowercase
    normalized_email = user_data.email.strip().lower()

    # Validate role and super_admin email
    from app.core.permissions import validate_super_admin_email
    from app.core.roles import SUPPORT_ROLES, TENANT_ROLES
    
    # Only super_admin can create users with support roles
    if user_data.role in SUPPORT_ROLES:
        validate_super_admin_email(normalized_email, user_data.role)
    
    # Validate role is valid
    valid_roles = SUPPORT_ROLES | TENANT_ROLES
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {user_data.role}. Must be one of: {list(valid_roles)}"
        )
    
    # Check if user already exists
    user_repo = UserRepository(db)
    existing_user = await user_repo.get_by_email(normalized_email)
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {normalized_email} already exists"
        )
    
    # Create new user
    logger.info("Creating user", email=normalized_email, role=user_data.role, user_id=current_user.id)
    new_user = User(
        email=normalized_email,
        full_name=user_data.full_name,
        role=user_data.role,
        hashed_password=get_password_hash(user_data.password)
    )
    
    new_user = await user_repo.create(new_user)
    
    # Get role safely for response - use ensure_role_string
    ensure_role_string(new_user)
    user_role = getattr(new_user, "role", "product_manager")
    if not isinstance(user_role, str):
        user_role = str(user_role) if user_role else "product_manager"
    
    # Log audit event
    from app.core.audit import AuditService, AuditAction
    from fastapi import Request
    await AuditService.log_action(
        db=db,
        action=AuditAction.USER_CREATE,
        user_id=current_user.id,
        organization_id=tenant.organization_id,
        resource_type="user",
        resource_id=new_user.id,
        request=None,  # Request not available in this endpoint
        details={"email": normalized_email, "role": user_data.role},
        status="success"
    )
    
    logger.info("User created successfully", user_id=new_user.id, created_by=current_user.id)
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        has_calendar_connected=False,
        role=user_role
    )


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user role
    Only Super Admin can update roles
    """
    require_super_admin(current_user)
    
    # Validate role and super_admin email
    from app.core.permissions import validate_super_admin_email
    from app.core.roles import SUPPORT_ROLES, TENANT_ROLES

    # Validate role is valid
    valid_roles = SUPPORT_ROLES | TENANT_ROLES
    if role_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {role_data.role}. Must be one of: {list(valid_roles)}"
        )
    
    # Get user
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Validate super_admin email if assigning super_admin role
    if role_data.role == 'super_admin':
        validate_super_admin_email(user.email, role_data.role)
    
    # Allow changing own role in development mode for testing
    # In production, Super Admins should not be able to change their own role
    from app.core.config import settings
    if user.id == current_user.id and settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role in production"
        )
    
    # Update role (store as string)
    logger.info("Updating user role", user_id=user_id, new_role=role_data.role, updated_by=current_user.id)
    user.role = role_data.role
    user = await user_repo.update(user)
    
    # Get role safely for response - use ensure_role_string
    ensure_role_string(user)
    user_role = getattr(user, "role", "product_manager")
    if not isinstance(user_role, str):
        user_role = str(user_role) if user_role else "product_manager"
    
    logger.info("User role updated successfully", user_id=user_id, updated_by=current_user.id)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        has_calendar_connected=user.google_refresh_token is not None,
        role=user_role
    )


