"""
Rate limiting configuration and utilities
"""

from fastapi import HTTPException, Request, status
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.logging import get_logger

logger = get_logger(__name__)

# Initialize limiter
# Use memory storage for now (in production, consider Redis)
limiter = Limiter(key_func=get_remote_address)


def get_tenant_identifier(request: Request) -> str:
    """
    Get tenant identifier for rate limiting
    Uses organization_id from user token if available, otherwise falls back to IP
    """
    # Try to get organization_id from request state (set by middleware)
    tenant_id = getattr(request.state, "organization_id", None)
    if tenant_id:
        return f"tenant:{tenant_id}"

    # Fallback to IP address
    return get_remote_address(request)


# Plan-based rate limits (requests per minute)
RATE_LIMITS_BY_PLAN: dict[str, dict[str, int]] = {
    "free": {
        "default": 60,  # 60 requests per minute
        "auth": 5,  # 5 login attempts per minute
        "create": 20,  # 20 create operations per minute
        "update": 30,  # 30 update operations per minute
        "ai": 5,  # 5 AI requests per minute (to control API costs)
    },
    "starter": {
        "default": 120,  # 120 requests per minute
        "auth": 10,
        "create": 40,
        "update": 60,
        "ai": 10,  # 10 AI requests per minute
    },
    "professional": {
        "default": 300,  # 300 requests per minute
        "auth": 20,
        "create": 100,
        "update": 150,
        "ai": 30,  # 30 AI requests per minute
    },
    "enterprise": {
        "default": 1000,  # 1000 requests per minute
        "auth": 50,
        "create": 500,
        "update": 750,
        "ai": 100,  # 100 AI requests per minute
    },
}


def get_rate_limit_for_plan(plan: str, limit_type: str = "default") -> int:
    """
    Get rate limit for a specific plan and limit type

    Args:
        plan: Subscription plan (free, starter, professional, enterprise)
        limit_type: Type of limit (default, auth, create, update)

    Returns:
        Rate limit (requests per minute)
    """
    plan_limits = RATE_LIMITS_BY_PLAN.get(plan, RATE_LIMITS_BY_PLAN["free"])
    return plan_limits.get(limit_type, plan_limits["default"])


async def get_rate_limit_for_request(request: Request, limit_type: str = "default") -> int:
    """
    Get rate limit for the current request based on user's plan

    Args:
        request: FastAPI request
        limit_type: Type of limit (default, auth, create, update)

    Returns:
        Rate limit (requests per minute)
    """
    # Try to get plan from request state (set by middleware)
    plan = getattr(request.state, "subscription_plan", "free")
    return get_rate_limit_for_plan(plan, limit_type)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors
    """
    logger.warning(
        "Rate limit exceeded",
        ip_address=get_remote_address(request),
        endpoint=request.url.path,
        organization_id=getattr(request.state, "organization_id", None),
    )

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"Rate limit exceeded: {exc.detail}"
    )
