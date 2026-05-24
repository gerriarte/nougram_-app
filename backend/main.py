"""
Main application entry point for Nougram Backend API
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

# Docs only in non-production
_docs_url = "/docs" if settings.ENVIRONMENT.lower() != "production" else None
_redoc_url = "/redoc" if settings.ENVIRONMENT.lower() != "production" else None
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.logging import get_logger
from app.core.permissions import PermissionError
from app.core.rate_limiting import limiter, rate_limit_exceeded_handler
from app.services.super_admin_bootstrap_service import ensure_super_admin_bootstrap

# Configure logging — INFO in dev, WARNING in production to reduce Railway log volume
_log_level = logging.INFO if settings.ENVIRONMENT.lower() != "production" else logging.WARNING
logging.basicConfig(level=_log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup schema creation is opt-in for local/dev only.
    # Default path across environments should be Alembic migrations.
    if settings.ENVIRONMENT.lower() != "production" and settings.CREATE_SCHEMA_ON_STARTUP:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Log CORS config for debugging (e.g. Railway production)
    origins = settings.cors_origins_list
    logger.info(
        "CORS configured",
        extra={
            "origin_count": len(origins),
            "origins_sample": [o[:30] + "..." if len(o) > 30 else o for o in origins[:3]],
        },
    )
    if not origins:
        logger.warning("CORS_ORIGINS is empty or invalid; cross-origin requests will be blocked")

    resend_api_key_present = bool((settings.RESEND_API_KEY or "").strip())
    resend_from_present = bool((settings.RESEND_FROM_EMAIL or "").strip())
    logger.info(
        "Email delivery provider",
        email_provider="resend",
        resend_api_key_present=resend_api_key_present,
        resend_from_email_present=resend_from_present,
    )
    if not resend_api_key_present:
        logger.warning("RESEND_API_KEY is empty; emails will not be delivered")
    if not resend_from_present:
        logger.warning("RESEND_FROM_EMAIL is empty; Resend sends will fail")

    # Optional startup bootstrap for super admin account.
    try:
        async with AsyncSessionLocal() as db:
            await ensure_super_admin_bootstrap(db)
    except Exception:
        logger.error(
            "Super admin bootstrap failed during startup",
            exc_info=True,
        )
    yield
    # Shutdown: Clean up if needed


# Create FastAPI application
app = FastAPI(
    title="Nougram API",
    description="""
    Backend API for Agency Profitability and Operations Platform.
    
    ## Features
    
    * **Multi-tenant SaaS**: Support for multiple organizations with tenant isolation
    * **Cost Management**: Track fixed costs, team salaries, and calculate blended cost rates
    * **Service Catalog**: Manage services with pricing strategies (hourly, fixed, recurring, project value)
    * **Project & Quote Management**: Create projects, calculate quotes with multiple pricing types
    * **Financial Projections**: Annual sales projections and break-even analysis
    * **Dashboard & Analytics**: KPIs, revenue analysis, and utilization metrics
    * **AI-Powered Features**: Onboarding suggestions, document parsing, natural language configuration
    * **Billing & Subscriptions**: Stripe integration for subscription management
    * **Role-Based Access Control**: Granular permissions for different user roles
    
    ## Authentication
    
    All endpoints require authentication via JWT Bearer token, except:
    * `/api/v1/auth/login`
    * `/api/v1/auth/register`
    * `/api/v1/organizations/register`
    
    ## Getting Started
    
    1. Register an organization at `/api/v1/organizations/register`
    2. Login at `/api/v1/auth/login` to get your access token
    3. Use the token in the Authorization header: `Authorization: Bearer <token>`
    4. Start managing your costs, services, and projects!
    
    ## Rate Limiting
    
    AI endpoints have rate limits based on subscription plan:
    * Free: 5 requests/minute
    * Starter: 10 requests/minute
    * Professional: 30 requests/minute
    * Enterprise: 100 requests/minute
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)


# Fallback CORS: ensure CORS headers on every response when Origin is allowed
# (handles proxies that may strip headers or OPTIONS not reaching app)
class CORSFallbackMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        origin = request.headers.get("origin")
        if not origin:
            return response
        allowed = settings.cors_origins_list
        if not allowed:
            return response
        if origin not in allowed:
            return response
        # Ensure CORS headers so preflight/actual responses are accepted by browser
        if "access-control-allow-origin" not in [h.lower() for h in response.headers.keys()]:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            )
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Max-Age"] = "3600"
        return response


# GZip compression for all responses ≥ 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure CORS (add fallback first so it runs outermost and can fix responses)
app.add_middleware(CORSFallbackMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Configure rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# Add PermissionError handler
@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError):
    """Handle PermissionError exceptions"""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)},
        headers={
            "Access-Control-Allow-Origin": settings.cors_origins_list[0]
            if settings.cors_origins_list
            else "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


# Include API router
app.include_router(api_router, prefix="/api/v1")


# Global exception handler to ensure CORS headers are always sent
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to ensure CORS headers are sent even on errors
    """
    logging.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
        headers={
            "Access-Control-Allow-Origin": settings.cors_origins_list[0]
            if settings.cors_origins_list
            else "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Nougram API is running", "version": "1.0.0", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}


@app.get("/health/ready")
async def health_ready():
    """
    Readiness probe: verifica conexión a BD.
    Uso: UptimeRobot, Kubernetes liveness, etc.
    """
    from sqlalchemy import text

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as e:
        logging.error("Readiness check failed", exc_info=True)
        detail = str(e) if settings.ENVIRONMENT.lower() != "production" else "database unavailable"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "error", "detail": detail},
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
