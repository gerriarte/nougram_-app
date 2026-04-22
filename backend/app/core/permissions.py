"""
Permissions system for multi-tenant platform

Implements role-based access control with two levels:
- Support roles: Multi-tenant managers
- Tenant roles: Client users within organizations
"""

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

if TYPE_CHECKING:
    pass

from app.core.config import settings
from app.core.roles import (
    SUPPORT_ROLES,
    TENANT_ROLES,
    get_role_type,
)
from app.models.user import User


class PermissionError(Exception):
    """Exception raised when user lacks required permission"""

    pass


def get_allowed_super_admin_emails() -> set[str]:
    """
    Resolve allowed emails for super_admin role assignment.

    Priority:
    1) SUPER_ADMIN_ALLOWED_EMAILS (comma-separated)
    2) SUPER_ADMIN_EMAIL (single value)
    """
    allowed: set[str] = set()

    raw_allowed = (settings.SUPER_ADMIN_ALLOWED_EMAILS or "").strip()
    if raw_allowed:
        for email in raw_allowed.split(","):
            normalized = email.strip().lower()
            if normalized:
                allowed.add(normalized)

    fallback_email = (settings.SUPER_ADMIN_EMAIL or "").strip().lower()
    if not allowed and fallback_email:
        allowed.add(fallback_email)

    return allowed


def validate_super_admin_email(email: str, role: str) -> None:
    """
    Validate that only the authorized email can be super_admin

    Args:
        email: User email
        role: Role being assigned

    Raises:
        HTTPException: If email is not authorized for super_admin role
    """
    if role == "super_admin":
        normalized_email = email.strip().lower()
        allowed_emails = get_allowed_super_admin_emails()
        if normalized_email not in allowed_emails:
            allowed_label = (
                ", ".join(sorted(allowed_emails))
                if allowed_emails
                else "configured super admin email"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Only {allowed_label} can be assigned the super_admin role",
            )


# Permission constants
PERM_ACCESS_ALL_TENANTS = "can_access_all_tenants"
PERM_VIEW_SENSITIVE_DATA = "can_view_sensitive_data"
PERM_MODIFY_COSTS = "can_modify_costs"
PERM_CREATE_QUOTES = "can_create_quotes"
PERM_SEND_QUOTES = "can_send_quotes"
PERM_MANAGE_SUBSCRIPTION = "can_manage_subscription"
PERM_INVITE_USERS = "can_invite_users"
PERM_CREATE_PROJECTS = "can_create_projects"
PERM_CREATE_SERVICES = "can_create_services"
PERM_DELETE_RESOURCES = "can_delete_resources"
PERM_VIEW_ANALYTICS = "can_view_analytics"
PERM_VIEW_FINANCIAL_PROJECTIONS = "can_view_financial_projections"

# Permission matrix: role -> set of permissions
PERMISSION_MATRIX: dict[str, set[str]] = {
    # Support roles
    "super_admin": {
        PERM_ACCESS_ALL_TENANTS,
        PERM_VIEW_SENSITIVE_DATA,
        PERM_MODIFY_COSTS,
        PERM_CREATE_QUOTES,
        PERM_SEND_QUOTES,
        PERM_MANAGE_SUBSCRIPTION,
        PERM_INVITE_USERS,
        PERM_CREATE_PROJECTS,
        PERM_CREATE_SERVICES,
        PERM_DELETE_RESOURCES,
        PERM_VIEW_ANALYTICS,
        PERM_VIEW_FINANCIAL_PROJECTIONS,  # Super admin should have access to all features
    },
    "support_manager": {
        PERM_ACCESS_ALL_TENANTS,
        # No sensitive data access (anonimizado)
        PERM_VIEW_ANALYTICS,
        # Limited modifications
    },
    "data_analyst": {
        # Only anonymized datasets
        PERM_VIEW_ANALYTICS,
    },
    # Tenant roles
    "owner": {
        PERM_VIEW_SENSITIVE_DATA,
        PERM_MODIFY_COSTS,
        PERM_CREATE_QUOTES,
        PERM_SEND_QUOTES,
        PERM_MANAGE_SUBSCRIPTION,
        PERM_INVITE_USERS,
        PERM_CREATE_PROJECTS,
        PERM_CREATE_SERVICES,
        PERM_DELETE_RESOURCES,
        PERM_VIEW_ANALYTICS,
        PERM_VIEW_FINANCIAL_PROJECTIONS,
    },
    "admin_financiero": {
        PERM_VIEW_SENSITIVE_DATA,
        PERM_MODIFY_COSTS,
        PERM_CREATE_QUOTES,
        PERM_SEND_QUOTES,
        PERM_CREATE_PROJECTS,
        PERM_CREATE_SERVICES,
        PERM_VIEW_ANALYTICS,
        PERM_VIEW_FINANCIAL_PROJECTIONS,
        # Cannot manage subscription or invite users
    },
    "product_manager": {
        PERM_CREATE_QUOTES,
        PERM_SEND_QUOTES,
        PERM_CREATE_PROJECTS,
        # Cannot view costs or manage services
        PERM_VIEW_ANALYTICS,
        # Cannot view financial projections (only owner and admin_financiero)
    },
    "collaborator": {
        PERM_CREATE_QUOTES,
        PERM_CREATE_PROJECTS,
        # Cannot send quotes, view costs, or analytics
    },
}

# Resources that consume credits (for future credit system)
CREDITS_REQUIRED: set[str] = {
    PERM_SEND_QUOTES,
    PERM_VIEW_ANALYTICS,  # Advanced analytics
}


def get_user_role(user: User) -> str | None:
    """
    Get user's role as a string

    Args:
        user: User model instance

    Returns:
        Role name or None
    """
    role = getattr(user, "role", None)
    if isinstance(role, str):
        return role
    return None


def get_user_role_type(user: User) -> str | None:
    """
    Get user's role_type ("support" or "tenant")

    Args:
        user: User model instance

    Returns:
        "support", "tenant", or None
    """
    role_type = getattr(user, "role_type", None)
    if role_type:
        return role_type

    # Infer from role if role_type is not set (backward compatibility)
    role = get_user_role(user)
    if role:
        return get_role_type(role)

    # Default to tenant for backward compatibility
    return "tenant"


def ensure_role_string(user: User) -> None:
    """
    Ensure user.role is a string (for backward compatibility)

    Args:
        user: User model instance
    """
    try:
        role = getattr(user, "role", None)
        if role is None or not isinstance(role, str):
            # Default to product_manager for tenant users
            role_type = get_user_role_type(user)
            if role_type == "support":
                user.role = "super_admin"
            else:
                user.role = "product_manager"
    except Exception:
        pass


def has_permission(user: User, permission: str) -> bool:
    """
    Check if user has a specific permission

    Args:
        user: User model instance
        permission: Permission name

    Returns:
        True if user has permission, False otherwise
    """
    role = get_user_role(user)
    if not role:
        return False

    role_permissions = PERMISSION_MATRIX.get(role, set())
    return permission in role_permissions


def check_permission(user: User, permission: str) -> None:
    """
    Check if user has permission, raise exception if not

    Args:
        user: User model instance
        permission: Permission name

    Raises:
        PermissionError: If user lacks permission
    """
    if not has_permission(user, permission):
        role = get_user_role(user) or "unknown"
        raise PermissionError(f"User with role '{role}' does not have permission '{permission}'")


def require_permission(user: User, permission: str) -> None:
    """
    Alias for check_permission (for consistency)

    Args:
        user: User model instance
        permission: Permission name

    Raises:
        PermissionError: If user lacks permission
    """
    check_permission(user, permission)


def can_user_access_tenant(user: User, tenant_id: int) -> bool:
    """
    Check if user can access a specific tenant/organization

    Args:
        user: User model instance
        tenant_id: Organization ID

    Returns:
        True if user can access tenant, False otherwise
    """
    role_type = get_user_role_type(user)

    # Support roles can access all tenants
    if role_type == "support" and has_permission(user, PERM_ACCESS_ALL_TENANTS):
        return True

    # Tenant users can only access their own organization
    user_org_id = getattr(user, "organization_id", None)
    return user_org_id == tenant_id


def can_create(user: User, resource: str) -> bool:
    """
    Check if user can create a specific resource

    Args:
        user: User model instance
        resource: Resource type ("project", "service", "quote", etc.)

    Returns:
        True if user can create resource, False otherwise
    """
    if resource == "project":
        return has_permission(user, PERM_CREATE_PROJECTS)
    elif resource == "service":
        return has_permission(user, PERM_CREATE_SERVICES)
    elif resource == "quote":
        return has_permission(user, PERM_CREATE_QUOTES)
    else:
        # Default: check if user has any create permission
        return has_permission(user, PERM_CREATE_QUOTES)


def can_edit(user: User, resource: str) -> bool:
    """
    Check if user can edit a specific resource

    Args:
        user: User model instance
        resource: Resource type

    Returns:
        True if user can edit resource, False otherwise
    """
    # For now, if user can create, they can edit
    # This can be refined later with specific edit permissions
    if resource in ["cost", "cost_fixed"]:
        return has_permission(user, PERM_MODIFY_COSTS)

    return can_create(user, resource)


def can_delete(user: User, resource: str) -> tuple[bool, bool]:
    """
    Check if user can delete a specific resource

    Args:
        user: User model instance
        resource: Resource type

    Returns:
        (can_delete, requires_approval)
    """
    can_delete_resource = has_permission(user, PERM_DELETE_RESOURCES)
    requires_approval = False  # Can be enhanced later

    return can_delete_resource, requires_approval


def can_approve_deletions(user: User) -> bool:
    """
    Check if user can approve deletion requests

    Args:
        user: User model instance

    Returns:
        True if user can approve deletions, False otherwise
    """
    role = get_user_role(user)
    # Only owners and super_admins can approve deletions
    return role in ["owner", "super_admin"]


def require_role(user: User, required_roles: list[str]) -> None:
    """
    Require user to have one of the specified roles

    Args:
        user: User model instance
        required_roles: List of allowed roles

    Raises:
        PermissionError: If user doesn't have required role
    """
    role = get_user_role(user)
    if not role or role not in required_roles:
        raise PermissionError(
            f"User must have one of these roles: {required_roles}. Current role: {role}"
        )


def require_super_admin(user: User) -> None:
    """
    Require user to be super_admin

    Args:
        user: User model instance

    Raises:
        PermissionError: If user is not super_admin
    """
    role = get_user_role(user)
    if role != "super_admin":
        raise PermissionError(f"Operation requires super_admin role. Current role: {role}")


def require_view_financial_projections(user: User) -> User:
    """
    Dependency function to require financial projections permission

    This function should be used as a dependency in FastAPI endpoints:
    ```python
    @router.get("/projections")
    async def get_projections(
        user: User = Depends(require_view_financial_projections)
    ):
        ...
    ```

    Args:
        user: Current user (from dependency)

    Returns:
        User instance if permission granted

    Raises:
        HTTPException: If user lacks permission
    """
    if not has_permission(user, PERM_VIEW_FINANCIAL_PROJECTIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view financial projections. Required roles: owner, admin_financiero",
        )
    return user


def requires_credits(permission: str) -> bool:
    """
    Check if a permission requires credits

    Args:
        permission: Permission name

    Returns:
        True if permission requires credits, False otherwise
    """
    return permission in CREDITS_REQUIRED


# Legacy compatibility: VALID_ROLES
VALID_ROLES = SUPPORT_ROLES | TENANT_ROLES
