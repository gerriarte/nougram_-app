"""
Permission middleware and decorators for FastAPI endpoints

Provides reusable decorators for permission checking in endpoints.
"""

from fastapi import Depends, HTTPException, status

from app.core.logging import get_logger
from app.core.permissions import (
    PERM_ACCESS_ALL_TENANTS,
    PERM_CREATE_PROJECTS,
    PERM_CREATE_QUOTES,
    PERM_CREATE_SERVICES,
    PERM_DELETE_RESOURCES,
    PERM_INVITE_USERS,
    PERM_MANAGE_SUBSCRIPTION,
    PERM_MODIFY_COSTS,
    PERM_SEND_QUOTES,
    PERM_VIEW_ANALYTICS,
    PERM_VIEW_FINANCIAL_PROJECTIONS,
    PERM_VIEW_SENSITIVE_DATA,
    PermissionError,
    check_permission,
    get_user_role,
    get_user_role_type,
)
from app.core.security import get_current_user
from app.models.user import User

logger = get_logger(__name__)


def require_permission_decorator(permission: str):
    """
    Create a dependency that requires a specific permission

    Usage:
        @router.get("/endpoint")
        async def my_endpoint(
            current_user: User = Depends(require_permission_decorator(PERM_MODIFY_COSTS)),
            ...
        ):
            ...
    """

    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        """Check if user has required permission"""
        try:
            check_permission(current_user, permission)
            return current_user
        except PermissionError as e:
            logger.warning(
                f"Permission denied: user {current_user.id} lacks permission {permission}",
                user_id=current_user.id,
                permission=permission,
                user_role=get_user_role(current_user),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission denied: {str(e)}"
            )

    return permission_checker


def require_role_decorator(allowed_roles: list[str]):
    """
    Create a dependency that requires one of the specified roles

    Usage:
        @router.get("/endpoint")
        async def my_endpoint(
            current_user: User = Depends(require_role_decorator(["owner", "admin_financiero"])),
            ...
        ):
            ...
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        """Check if user has one of the required roles"""
        user_role = get_user_role(current_user)

        if not user_role or user_role not in allowed_roles:
            logger.warning(
                f"Role denied: user {current_user.id} has role {user_role}, required one of {allowed_roles}",
                user_id=current_user.id,
                user_role=user_role,
                required_roles=allowed_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires one of these roles: {', '.join(allowed_roles)}. Your role: {user_role}",
            )

        return current_user

    return role_checker


def require_support_role_decorator(allowed_support_roles: list[str] = None):
    """
    Create a dependency that requires a support role (optionally specific support roles)

    Usage:
        @router.get("/endpoint")
        async def my_endpoint(
            current_user: User = Depends(require_support_role_decorator(["super_admin", "support_manager"])),
            ...
        ):
            ...
    """

    async def support_role_checker(current_user: User = Depends(get_current_user)) -> User:
        """Check if user is a support role (and optionally one of the specified support roles)"""
        user_role = get_user_role(current_user)
        role_type = get_user_role_type(current_user)

        # Check if user is a support role
        if role_type != "support" and user_role != "super_admin":
            logger.warning(
                f"Support role required: user {current_user.id} is not a support role",
                user_id=current_user.id,
                user_role=user_role,
                role_type=role_type,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This endpoint requires a support role (super_admin, support_manager, or data_analyst)",
            )

        # If specific support roles are required, check them
        if allowed_support_roles and user_role not in allowed_support_roles:
            logger.warning(
                f"Specific support role required: user {current_user.id} has role {user_role}, required one of {allowed_support_roles}",
                user_id=current_user.id,
                user_role=user_role,
                required_roles=allowed_support_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires one of these support roles: {', '.join(allowed_support_roles)}",
            )

        return current_user

    return support_role_checker


# Convenience dependencies for common permission checks
require_view_sensitive_data = require_permission_decorator(PERM_VIEW_SENSITIVE_DATA)
require_modify_costs = require_permission_decorator(PERM_MODIFY_COSTS)
require_create_quotes = require_permission_decorator(PERM_CREATE_QUOTES)
require_send_quotes = require_permission_decorator(PERM_SEND_QUOTES)
require_manage_subscription = require_permission_decorator(PERM_MANAGE_SUBSCRIPTION)
require_invite_users = require_permission_decorator(PERM_INVITE_USERS)
require_create_projects = require_permission_decorator(PERM_CREATE_PROJECTS)
require_create_services = require_permission_decorator(PERM_CREATE_SERVICES)
require_delete_resources = require_permission_decorator(PERM_DELETE_RESOURCES)
require_view_analytics = require_permission_decorator(PERM_VIEW_ANALYTICS)
require_view_financial_projections = require_permission_decorator(PERM_VIEW_FINANCIAL_PROJECTIONS)
require_access_all_tenants = require_permission_decorator(PERM_ACCESS_ALL_TENANTS)

# Convenience dependencies for common role checks
require_owner_or_admin = require_role_decorator(["owner", "admin_financiero"])
require_owner_only = require_role_decorator(["owner"])
require_super_admin = require_role_decorator(["super_admin"])
