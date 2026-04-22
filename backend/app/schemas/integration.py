"""
Pydantic schemas for Integrations
"""

from pydantic import BaseModel, Field


class GoogleSheetsSyncRequest(BaseModel):
    """Schema for Google Sheets sync request"""

    sheet_id: str | None = Field(
        None, description="Google Sheets ID (uses default if not provided)"
    )
    range: str | None = Field(None, description="Range to sync (e.g., 'Sheet1!A1:Z100')")


class GoogleSheetsSyncResponse(BaseModel):
    """Schema for Google Sheets sync response"""

    success: bool = Field(..., description="Whether sync was successful")
    message: str = Field(..., description="Sync status message")
    records_synced: int = Field(default=0, description="Number of records synced")
    errors: list[str] = Field(default_factory=list, description="List of errors if any")
