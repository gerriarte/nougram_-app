"""
Third-party integrations endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.sheets import sync_google_sheets_data
from app.core.tenant import TenantContext, get_tenant_context
from app.models.user import User
from app.schemas.integration import (
    GoogleSheetsSyncRequest,
    GoogleSheetsSyncResponse,
)

router = APIRouter()


@router.post("/sheets/sync", response_model=GoogleSheetsSyncResponse)
async def sync_google_sheets_endpoint(
    request: GoogleSheetsSyncRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Sync data from Google Sheets

    This endpoint syncs data from a Google Sheet (costs, team members, etc.)
    using the configured Service Account. Data is synced to the current organization.

    Multi-tenant: All synced data is scoped to the user's organization.
    """
    try:
        result = await sync_google_sheets_data(
            sheet_id=request.sheet_id,
            range_name=request.range,
            organization_id=tenant.organization_id,  # Multi-tenant: scope to organization
            db=db,
        )

        return GoogleSheetsSyncResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            records_synced=result.get("records_synced", 0),
            errors=result.get("errors", []),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing Google Sheets: {str(e)}",
        )
