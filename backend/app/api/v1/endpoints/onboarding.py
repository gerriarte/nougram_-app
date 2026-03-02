"""
Onboarding endpoints
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant import get_tenant_context, TenantContext
from app.core.permission_middleware import require_modify_costs
from app.models.user import User
from app.controllers.onboarding_controller import OnboardingController
from app.schemas.onboarding import (
    BenchmarksResponse,
    CompleteOnboardingRequest,
    CompleteOnboardingResponse,
    TemporaryBCRRequest,
    TemporaryBCRResponse
)

router = APIRouter()


@router.get(
    "/templates",
    summary="Get onboarding inventory templates"
)
async def get_onboarding_templates(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get onboarding inventory template catalog from backend source.
    """
    controller = OnboardingController(db, tenant, current_user)
    return await controller.get_templates()


@router.get(
    "/benchmarks",
    response_model=BenchmarksResponse,
    summary="Get benchmarks for a business profile"
)
async def get_benchmarks(
    profile_type: str = Query(..., description="Profile type: freelance, company, or agency"),
    country: Optional[str] = Query(None, description="Country code (defaults to organization country)"),
    currency: Optional[str] = Query(None, description="Currency code (defaults to organization currency)"),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get benchmark values for a business profile type
    
    Returns industry-standard benchmarks for:
    - Average monthly income (freelance)
    - Average margin percentage
    - Average billable hours per month
    - Average team size (company/agency)
    - Average salary (company/agency)
    - Average number of clients (agency)
    
    **Permissions:**
    - Requires authentication
    - Available to all authenticated users
    
    **Example:**
    ```
    GET /api/v1/onboarding/benchmarks?profile_type=freelance&country=US&currency=USD
    ```
    """
    controller = OnboardingController(db, tenant, current_user)
    return await controller.get_benchmarks(
        profile_type=profile_type,
        country=country,
        currency=currency
    )


@router.post(
    "/complete",
    response_model=CompleteOnboardingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Complete onboarding by saving all configuration"
)
async def complete_onboarding(
    request: CompleteOnboardingRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(require_modify_costs),  # Require permission to modify costs
    db: AsyncSession = Depends(get_db)
):
    """
    Complete onboarding by saving all configuration in a single transaction
    
    This endpoint:
    1. Updates organization details (name, currency, settings)
    2. Creates all team members
    3. Creates all operational expenses (fixed costs)
    4. Calculates and returns the final BCR
    
    **Permissions:**
    - Requires `can_modify_costs` permission (team and costs affect financial calculations)
    - Allowed roles: owner, admin_financiero
    - Must be owner of the organization
    
    **Request Body:**
    - `organization_name`: Organization name (optional if already set)
    - `country`: Country code (required)
    - `currency`: Currency code (required)
    - `profile_type`: Profile type (required)
    - `team_members`: List of team members (can be empty for freelance)
    - `expenses`: List of operational expenses (optional)
    - `tax_structure`: Tax structure dictionary (optional)
    - `social_charges_config`: Social charges configuration (optional)
    
    **Returns:**
    - `201 Created`: Onboarding completed successfully
    - `400 Bad Request`: Validation error
    - `403 Forbidden`: User doesn't have permission
    """
    # Verify user is owner or admin_financiero
    if current_user.role not in ['owner', 'admin_financiero']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners and financial admins can complete onboarding"
        )
    
    controller = OnboardingController(db, tenant, current_user)
    return await controller.complete_onboarding(request)


@router.post(
    "/calculate-bcr",
    response_model=TemporaryBCRResponse,
    summary="Calculate BCR with temporary onboarding data"
)
async def calculate_temporary_bcr(
    request: TemporaryBCRRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate BCR with temporary onboarding data (before saving)
    
    This endpoint allows calculating the BCR with data that hasn't been saved yet,
    useful for showing a preview in the onboarding flow.
    
    **Permissions:**
    - Requires authentication
    - Available to all authenticated users
    
    **Request Body:**
    - `team_members`: List of team members (at least one required)
    - `expenses`: List of operational expenses (optional)
    - `currency`: Currency code (required)
    
    **Returns:**
    - `200 OK`: BCR calculated successfully
    - `400 Bad Request`: Validation error (e.g., no team members)
    
    **Note:**
    This is a temporary calculation and may differ from the actual BCR after saving,
    especially if there are existing team members or costs in the database.
    """
    controller = OnboardingController(db, tenant, current_user)
    return await controller.calculate_temporary_bcr(request)
