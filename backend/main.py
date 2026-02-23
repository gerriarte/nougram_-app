"""
Main application entry point for Nougram Backend API
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import settings

# Docs only in non-production
_docs_url = "/docs" if settings.ENVIRONMENT.lower() != "production" else None
_redoc_url = "/redoc" if settings.ENVIRONMENT.lower() != "production" else None
from app.core.database import engine, Base
from app.core.database import AsyncSessionLocal
from app.api.v1.router import api_router
from app.core.rate_limiting import limiter, rate_limit_exceeded_handler
from app.core.permissions import PermissionError
from app.core.logging import get_logger
from app.services.super_admin_bootstrap_service import ensure_super_admin_bootstrap
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup: Create database tables only in non-production (use Alembic in production)
    if settings.ENVIRONMENT.lower() != "production":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

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
    redoc_url=_redoc_url
)

# Configure CORS
# CORS must be added before other middleware
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
        content={
            "detail": str(exc)
        },
        headers={
            "Access-Control-Allow-Origin": settings.cors_origins_list[0] if settings.cors_origins_list else "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
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
        content={
            "detail": f"Internal server error: {str(exc)}"
        },
        headers={
            "Access-Control-Allow-Origin": settings.cors_origins_list[0] if settings.cors_origins_list else "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Nougram API is running",
        "version": "1.0.0",
        "status": "healthy"
    }


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
