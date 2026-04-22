"""
Delete request management endpoints
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.delete_request import (
    DeleteRequestApprovalRequest,
    DeleteRequestListResponse,
    DeleteRequestResponse,
)

logger = logging.getLogger(__name__)
DELETE_REQUESTS_ENABLED = False

router = APIRouter()


@router.get("/pending-count", response_model=int)
async def get_pending_count(
    current_user: User = Depends(get_current_user),
    _db: AsyncSession = Depends(get_db),
):
    """
    Get count of pending delete requests
    - Super Admin: Gets total pending count
    - Others: Gets their own pending count
    Returns 0 if delete_requests table doesn't exist (rollback state)
    """
    if not DELETE_REQUESTS_ENABLED:
        logger.debug("Delete requests disabled; returning 0 pending count")
        return 0

    # Feature disabled fallback
    return 0


@router.get("/", response_model=DeleteRequestListResponse)
async def list_delete_requests(
    status_filter: str | None = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    _db: AsyncSession = Depends(get_db),
):
    """
    List delete requests
    - Super Admin: Can see all requests
    - Others: Can only see their own requests
    """
    if not DELETE_REQUESTS_ENABLED:
        logger.debug("Delete requests disabled; returning empty list")
        return DeleteRequestListResponse(items=[], total=0)

    return DeleteRequestListResponse(items=[], total=0)


@router.get("/{request_id}", response_model=DeleteRequestResponse)
async def get_delete_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    _db: AsyncSession = Depends(get_db),
):
    """
    Get a specific delete request
    """
    if not DELETE_REQUESTS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Delete requests feature is disabled",
        )

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Delete requests feature is disabled"
    )


@router.post("/{request_id}/approve", response_model=DeleteRequestResponse)
async def approve_delete_request(
    request_id: int,
    approval_data: DeleteRequestApprovalRequest | None = None,
    current_user: User = Depends(get_current_user),
    _db: AsyncSession = Depends(get_db),
):
    """
    Approve a delete request (Super Admin only)
    """
    if not DELETE_REQUESTS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Delete requests feature is disabled",
        )

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Delete requests feature is disabled"
    )


@router.post("/{request_id}/reject", response_model=DeleteRequestResponse)
async def reject_delete_request(
    request_id: int,
    rejection_data: DeleteRequestApprovalRequest,
    current_user: User = Depends(get_current_user),
    _db: AsyncSession = Depends(get_db),
):
    """
    Reject a delete request (Super Admin only)
    """
    if not DELETE_REQUESTS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Delete requests feature is disabled",
        )

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Delete requests feature is disabled"
    )


async def _perform_deletion(delete_request, _db: AsyncSession):
    """
    Actually perform the deletion based on resource type
    """
    logger.debug("_perform_deletion invoked but feature is disabled; no action taken")
    return
