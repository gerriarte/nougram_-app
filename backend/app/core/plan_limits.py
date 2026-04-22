"""
Plan limits and validation for multi-tenant subscriptions
"""

from typing import Any

from fastapi import HTTPException, status

# Plan limits configuration
PLAN_LIMITS: dict[str, dict[str, int]] = {
    "free": {
        "max_users": 1,
        "max_projects": 5,
        "max_services": 10,
        "max_team_members": 3,
        "credits_per_month": 10,
    },
    "starter": {
        "max_users": 5,
        "max_projects": 10,
        "max_services": 50,
        "max_team_members": 10,
        "credits_per_month": 100,
    },
    "professional": {
        "max_users": 20,
        "max_projects": 20,
        "max_services": 200,
        "max_team_members": 50,
        "credits_per_month": 500,
    },
    "enterprise": {
        "max_users": -1,  # Unlimited
        "max_projects": -1,  # Unlimited
        "max_services": -1,  # Unlimited
        "max_team_members": -1,  # Unlimited
        "credits_per_month": -1,  # Unlimited
    },
}


def get_plan_limit(plan: str, limit_type: str) -> int:
    """
    Get limit for a specific plan and limit type

    Args:
        plan: Subscription plan (free, starter, professional, enterprise)
        limit_type: Type of limit (max_users, max_projects, max_services, max_team_members)

    Returns:
        Limit value (-1 means unlimited)
    """
    plan_limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    return plan_limits.get(limit_type, 0)


def is_unlimited(limit: int) -> bool:
    """Check if limit is unlimited (-1)"""
    return limit == -1


def check_limit(current_count: int, limit: int, resource_name: str, plan: str) -> None:
    """
    Check if current count exceeds limit

    Args:
        current_count: Current number of resources
        limit: Maximum allowed (or -1 for unlimited)
        resource_name: Name of the resource for error messages
        plan: Subscription plan for error messages

    Raises:
        HTTPException 403: If limit is exceeded
    """
    if is_unlimited(limit):
        return  # No limit

    if current_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Plan limit exceeded: {resource_name}. "
                f"Current: {current_count}, Limit: {limit}. "
                f"Your current plan ({plan}) allows up to {limit} {resource_name}. "
                f"Please upgrade your plan to increase limits."
            ),
        )


async def validate_user_limit(organization_id: int, plan: str, db) -> None:
    """
    Validate that organization hasn't exceeded user limit

    Args:
        organization_id: Organization ID
        plan: Subscription plan
        db: Database session

    Raises:
        HTTPException 403: If user limit is exceeded
    """
    from sqlalchemy import func, select

    from app.models.user import User

    limit = get_plan_limit(plan, "max_users")
    if is_unlimited(limit):
        return

    result = await db.execute(
        select(func.count(User.id)).where(User.organization_id == organization_id)
    )
    current_count = result.scalar() or 0

    check_limit(current_count, limit, "users", plan)


async def validate_project_limit(organization_id: int, plan: str, db) -> None:
    """
    Validate that organization hasn't exceeded project limit

    Args:
        organization_id: Organization ID
        plan: Subscription plan
        db: Database session

    Raises:
        HTTPException 403: If project limit is exceeded
    """
    from sqlalchemy import func, select

    from app.models.project import Project

    limit = get_plan_limit(plan, "max_projects")
    if is_unlimited(limit):
        return

    result = await db.execute(
        select(func.count(Project.id)).where(
            Project.organization_id == organization_id,
            Project.deleted_at.is_(None),  # Only count non-deleted projects
        )
    )
    current_count = result.scalar() or 0

    check_limit(current_count, limit, "projects", plan)


async def validate_service_limit(organization_id: int, plan: str, db) -> None:
    """
    Validate that organization hasn't exceeded service limit

    Args:
        organization_id: Organization ID
        plan: Subscription plan
        db: Database session

    Raises:
        HTTPException 403: If service limit is exceeded
    """
    from sqlalchemy import func, select

    from app.models.service import Service

    limit = get_plan_limit(plan, "max_services")
    if is_unlimited(limit):
        return

    result = await db.execute(
        select(func.count(Service.id)).where(
            Service.organization_id == organization_id,
            Service.deleted_at.is_(None),  # Only count non-deleted services
        )
    )
    current_count = result.scalar() or 0

    check_limit(current_count, limit, "services", plan)


async def validate_team_member_limit(organization_id: int, plan: str, db) -> None:
    """
    Validate that organization hasn't exceeded team member limit

    Args:
        organization_id: Organization ID
        plan: Subscription plan
        db: Database session

    Raises:
        HTTPException 403: If team member limit is exceeded
    """
    from sqlalchemy import func, select

    from app.models.team import TeamMember

    limit = get_plan_limit(plan, "max_team_members")
    if is_unlimited(limit):
        return

    result = await db.execute(
        select(func.count(TeamMember.id)).where(
            TeamMember.organization_id == organization_id,
            TeamMember.is_active,  # Only count active team members
        )
    )
    current_count = result.scalar() or 0

    check_limit(current_count, limit, "team members", plan)


# Plan information including prices, features, and limits
PLAN_INFO: dict[str, dict[str, Any]] = {
    "free": {
        "display_name": "Free",
        "description": "Perfect for trying out Nougram",
        "monthly_price": 0,
        "yearly_price": 0,
        "features": [
            "Up to 1 user",
            "Up to 5 projects",
            "Up to 10 services",
            "Up to 3 team members",
            "Basic quote generation",
            "PDF export",
        ],
        "limits": {
            "max_users": 1,
            "max_projects": 5,
            "max_services": 10,
            "max_team_members": 3,
            "credits_per_month": 10,
        },
    },
    "starter": {
        "display_name": "Starter",
        "description": "Ideal for small teams getting started",
        "monthly_price": 29.99,
        "yearly_price": 299.99,  # ~2 months free
        "features": [
            "Up to 5 users",
            "Up to 10 projects",
            "Up to 50 services",
            "Up to 10 team members",
            "Advanced quote generation",
            "PDF and DOCX export",
            "Email quotes",
            "Basic analytics",
        ],
        "limits": {
            "max_users": 5,
            "max_projects": 10,
            "max_services": 50,
            "max_team_members": 10,
            "credits_per_month": 100,
        },
    },
    "professional": {
        "display_name": "Professional",
        "description": "For growing agencies and teams",
        "monthly_price": 99.99,
        "yearly_price": 999.99,  # ~2 months free
        "features": [
            "Up to 20 users",
            "Up to 20 projects",
            "Up to 200 services",
            "Up to 50 team members",
            "Advanced quote generation",
            "PDF and DOCX export",
            "Email quotes",
            "Advanced analytics",
            "Custom templates",
            "Priority support",
        ],
        "limits": {
            "max_users": 20,
            "max_projects": 20,
            "max_services": 200,
            "max_team_members": 50,
            "credits_per_month": 500,
        },
    },
    "enterprise": {
        "display_name": "Enterprise",
        "description": "Unlimited everything for large organizations",
        "monthly_price": None,  # Contact for pricing
        "yearly_price": None,
        "features": [
            "Unlimited users",
            "Unlimited projects",
            "Unlimited services",
            "Unlimited team members",
            "Advanced quote generation",
            "PDF and DOCX export",
            "Email quotes",
            "Advanced analytics",
            "Custom templates",
            "Dedicated support",
            "Custom integrations",
            "SLA guarantee",
            "On-premise deployment options",
        ],
        "limits": {
            "max_users": -1,  # Unlimited
            "max_projects": -1,
            "max_services": -1,
            "max_team_members": -1,
            "credits_per_month": -1,  # Unlimited
        },
    },
}
