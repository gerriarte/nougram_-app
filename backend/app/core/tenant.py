"""
Tenant Context for multi-tenant architecture
Manages organization context and isolation
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.core.logging import get_logger

logger = get_logger(__name__)


class TenantContext:
    """
    Tenant context containing organization information
    Used to isolate data access by organization
    """
    def __init__(self, organization_id: int, organization: Organization):
        self.organization_id = organization_id
        self.organization = organization
        self.subscription_plan = organization.subscription_plan
        self.subscription_status = organization.subscription_status
    
    def is_active(self) -> bool:
        """Check if organization subscription is active"""
        return self.subscription_status == "active"
    
    def __repr__(self):
        return f"TenantContext(org_id={self.organization_id}, plan={self.subscription_plan}, status={self.subscription_status})"


async def get_tenant_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TenantContext:
    """
    Dependency to get tenant context from current user
    
    Validates that:
    1. User has an organization_id (if role_type is "tenant")
    2. Organization exists
    3. Organization subscription is active (can be bypassed for super_admin)
    
    Returns:
        TenantContext with organization information
    
    Raises:
        HTTPException 400: If tenant user has no organization
        HTTPException 404: If organization not found
        HTTPException 403: If organization subscription is not active
    """
    from app.core.permissions import get_user_role_type
    
    # Get role_type
    role_type = get_user_role_type(current_user)
    
    # Support users can carry active org context in a transient attribute from JWT.
    # Tenant users must use their persisted organization_id.
    active_org_id = getattr(current_user, "active_organization_id", None)
    organization_id = active_org_id if active_org_id is not None else getattr(current_user, "organization_id", None)
    
    if role_type == "tenant" and organization_id is None:
        logger.error(f"Tenant user {current_user.id} has no organization_id")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant users must belong to an organization"
        )
    
    if organization_id is None:
        # Support users must switch/select an active organization before tenant-scoped operations.
        logger.warning(f"Support user {current_user.id} has no active organization context")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active organization selected. Use switch-organization first."
        )
    
    # Load organization with all details
    result = await db.execute(
        select(Organization)
        .where(Organization.id == organization_id)
    )
    organization = result.scalar_one_or_none()
    
    if organization is None:
        logger.error(f"Organization {organization_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found"
        )
    
    # Check subscription status (allow support roles to bypass)
    from app.core.permissions import get_user_role
    user_role = get_user_role(current_user)
    is_support_user = role_type == "support" or user_role == "super_admin"
    
    if not organization.subscription_status == "active" and not is_support_user:
        logger.warning(
            f"User {current_user.id} accessing organization {organization_id} with status {organization.subscription_status}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Organization subscription is {organization.subscription_status}. Please contact support."
        )
    
    tenant_context = TenantContext(
        organization_id=organization.id,
        organization=organization
    )
    
    logger.info(
        f"Tenant context created for user {current_user.id}",
        organization_id=tenant_context.organization_id,
        plan=tenant_context.subscription_plan
    )
    
    return tenant_context









