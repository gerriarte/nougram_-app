"""
Locale detection middleware for FastAPI
Extracts locale from request headers and makes it available via dependency
"""

from fastapi import Request

from app.core.translations import get_locale_from_request


def get_locale(request: Request) -> str:
    """
    Dependency function to get locale from request

    Args:
        request: FastAPI Request object

    Returns:
        Locale code (e.g., 'es', 'en')
    """
    return get_locale_from_request(request)


async def locale_middleware(request: Request, call_next):
    """
    ASGI middleware to add locale to request state

    Args:
        request: FastAPI Request object
        call_next: Next middleware/route handler

    Returns:
        Response with locale in state
    """
    locale = get_locale_from_request(request)
    request.state.locale = locale
    response = await call_next(request)
    return response
