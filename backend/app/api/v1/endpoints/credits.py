"""
Credit management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant import get_tenant_context, TenantContext
from app.core.permissions import require_super_admin, get_user_role
from app.core.logging import get_logger
from app.models.user import User
from app.services.credit_service import CreditService
from app.repositories.credit_transaction_repository import CreditTransactionRepository
from app.schemas.credit import (
    CreditBalanceResponse,
    CreditTransactionResponse,
    CreditTransactionListResponse,
    GrantManualCreditsRequest,
    ResetCreditsRequest
)

logger = get_logger(__name__)

router = APIRouter()


@router.get("/me/balance", response_model=CreditBalanceResponse, summary="Get my organization's credit balance")
async def get_my_credit_balance(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get credit balance for the current user's organization
    
    **Permissions:**
    - All authenticated users can view their organization's credit balance
    
    **Returns:**
    - `200 OK`: Credit balance information
    """
    balance = await CreditService.get_credit_balance(tenant.organization_id, db)
    return CreditBalanceResponse(**balance)


@router.get("/me/history", response_model=CreditTransactionListResponse, summary="Get credit transaction history")
async def get_my_credit_history(
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)")
):
    """
    Get credit transaction history for the current user's organization
    
    **Permissions:**
    - All authenticated users can view their organization's transaction history
    
    **Returns:**
    - `200 OK`: List of credit transactions
    """
    transaction_repo = CreditTransactionRepository(db)
    offset = (page - 1) * page_size
    
    transactions = await transaction_repo.get_by_organization_id(
        organization_id=tenant.organization_id,
        limit=page_size,
        offset=offset
    )
    
    # Get total count efficiently at DB level
    total = await transaction_repo.count_by_organization_id(tenant.organization_id)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return CreditTransactionListResponse(
        items=[CreditTransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


# Admin endpoints - these should be mounted under /admin/organizations/{org_id}/credits
# But for now, we'll use /admin/credits/{organization_id} pattern

@router.get("/admin/{organization_id}/balance", response_model=CreditBalanceResponse, summary="[Admin] Get organization credit balance")
async def get_organization_credit_balance(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get credit balance for a specific organization (Admin only)
    
    **Permissions:**
    - **Super Admin**: Allowed
    - **All other users**: Forbidden
    
    **Returns:**
    - `200 OK`: Credit balance information
    - `403 Forbidden`: User doesn't have permission
    - `404 Not Found`: Organization not found
    """
    require_super_admin(current_user)
    
    # Verify organization exists
    from sqlalchemy import select
    from app.models.organization import Organization
    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} not found"
        )
    
    balance = await CreditService.get_credit_balance(organization_id, db)
    return CreditBalanceResponse(**balance)


@router.post("/admin/{organization_id}/grant", response_model=CreditBalanceResponse, summary="[Admin] Grant manual credits")
async def grant_manual_credits(
    organization_id: int,
    request: GrantManualCreditsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Grant manual credits to an organization (Admin only)
    
    **Permissions:**
    - **Super Admin**: Allowed
    - **All other users**: Forbidden
    
    **Request Body:**
    - `amount`: Number of credits to grant (must be positive)
    - `reason`: Reason for granting credits
    
    **Returns:**
    - `200 OK`: Updated credit balance
    - `403 Forbidden`: User doesn't have permission
    - `404 Not Found`: Organization not found
    """
    require_super_admin(current_user)
    
    # Verify organization exists
    from sqlalchemy import select
    from app.models.organization import Organization
    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} not found"
        )
    
    await CreditService.grant_manual_credits(
        organization_id=organization_id,
        amount=request.amount,
        granted_by=current_user.id,
        reason=request.reason,
        db=db
    )
    
    balance = await CreditService.get_credit_balance(organization_id, db)
    return CreditBalanceResponse(**balance)


@router.get("/admin/{organization_id}/transactions", response_model=CreditTransactionListResponse, summary="[Admin] Get organization transaction history")
async def get_organization_credit_transactions(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)")
):
    """
    Get credit transaction history for a specific organization (Admin only)
    
    **Permissions:**
    - **Super Admin**: Allowed
    - **All other users**: Forbidden
    
    **Returns:**
    - `200 OK`: List of credit transactions
    - `403 Forbidden`: User doesn't have permission
    - `404 Not Found`: Organization not found
    """
    require_super_admin(current_user)
    
    # Verify organization exists
    from sqlalchemy import select
    from app.models.organization import Organization
    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} not found"
        )
    
    transaction_repo = CreditTransactionRepository(db)
    offset = (page - 1) * page_size
    
    transactions = await transaction_repo.get_by_organization_id(
        organization_id=organization_id,
        limit=page_size,
        offset=offset
    )
    
    # Get total count efficiently at DB level
    total = await transaction_repo.count_by_organization_id(organization_id)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return CreditTransactionListResponse(
        items=[CreditTransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/admin/{organization_id}/reset", response_model=CreditBalanceResponse, summary="[Admin] Manually reset monthly credits")
async def reset_monthly_credits(
    organization_id: int,
    request: ResetCreditsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger monthly credit reset for an organization (Admin only)
    
    This forces a monthly reset, granting new credits according to the organization's plan.
    
    **Permissions:**
    - **Super Admin**: Allowed
    - **All other users**: Forbidden
    
    **Returns:**
    - `200 OK`: Updated credit balance after reset
    - `403 Forbidden`: User doesn't have permission
    - `404 Not Found`: Organization not found
    """
    require_super_admin(current_user)
    
    # Verify organization exists
    from sqlalchemy import select
    from app.models.organization import Organization
    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} not found"
        )
    
    await CreditService.grant_subscription_credits(organization_id, db, force=True)
    
    balance = await CreditService.get_credit_balance(organization_id, db)
    return CreditBalanceResponse(**balance)






