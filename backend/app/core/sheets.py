"""
Google Sheets integration utilities
"""

import gspread
from google.oauth2.service_account import Credentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.currency import DEFAULT_CURRENCY, is_valid_currency, resolve_primary_currency
from app.core.logging import get_logger
from app.models.cost import CostFixed
from app.models.organization import Organization
from app.models.team import TeamMember

logger = get_logger(__name__)


async def resolve_import_currency(db: AsyncSession, organization_id: int | None) -> str:
    """
    Moneda por defecto de una importación: la moneda primaria de la organización.

    Defaultear a USD en una org que opera en COP guarda el sueldo de 6.000.000 COP
    como 6.000.000 USD, y el BCR lo normaliza multiplicando por la tasa (4000x).
    """
    if db is None or organization_id is None:
        return DEFAULT_CURRENCY
    try:
        result = await db.execute(select(Organization).where(Organization.id == organization_id))
        org = result.scalar_one_or_none()
    except Exception as e:  # pragma: no cover - defensivo, la sync no debe caerse por esto
        logger.error(f"Error resolving import currency for org {organization_id}: {e}")
        return DEFAULT_CURRENCY
    return resolve_primary_currency(org)


def row_currency(row: dict) -> str | None:
    """
    Moneda declarada en la fila de la hoja, o None si no dice nada usable.

    Un código no soportado se descarta con log: guardarlo crudo lo vuelve
    indistinguible de USD para normalize_to_primary_currency.
    """
    raw = str(row.get("currency") or "").strip().upper()
    if not raw:
        return None
    if not is_valid_currency(raw):
        logger.warning(f"Google Sheets import: unsupported currency '{raw}' ignored")
        return None
    return raw


def get_sheets_client() -> gspread.Client | None:
    """
    Get Google Sheets client using Service Account

    Returns:
        gspread.Client instance or None if error
    """
    try:
        # Load credentials from service account JSON file
        creds = Credentials.from_service_account_file(
            settings.GOOGLE_SERVICE_ACCOUNT_PATH,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )

        client = gspread.authorize(creds)
        return client

    except Exception as e:
        logger.error(f"Error getting Google Sheets client: {e}", exc_info=True)
        return None


async def sync_google_sheets_data(
    sheet_id: str | None = None,
    range_name: str | None = None,
    organization_id: int | None = None,
    db: AsyncSession = None,
) -> dict:
    """
    Sync data from Google Sheets to database

    Args:
        sheet_id: Google Sheets ID (uses default from config if not provided)
        range_name: Range to sync (e.g., 'Sheet1!A1:Z100')
        organization_id: Organization ID for tenant scoping (required for multi-tenant)
        db: Database session

    Returns:
        Dict with sync results
    """
    try:
        client = get_sheets_client()

        if not client:
            return {
                "success": False,
                "message": "Failed to initialize Google Sheets client",
                "records_synced": 0,
                "errors": ["Could not authenticate with Google Sheets"],
            }

        # Use configured sheet ID or provided one
        sheet_id_to_use = sheet_id or settings.GOOGLE_SHEETS_ID

        if not sheet_id_to_use:
            return {
                "success": False,
                "message": "No Google Sheets ID provided",
                "records_synced": 0,
                "errors": ["GOOGLE_SHEETS_ID not configured"],
            }

        # Open the spreadsheet
        spreadsheet = client.open_by_key(sheet_id_to_use)

        records_synced = 0
        errors = []

        # Moneda por defecto de la importación = la primaria del tenant, no "USD".
        default_currency = await resolve_import_currency(db, organization_id)

        # Sync Fixed Costs (from "Costs" sheet)
        try:
            costs_sheet = spreadsheet.worksheet("Costs")
            costs_data = costs_sheet.get_all_records()

            for row in costs_data:
                try:
                    # Check if cost already exists (with tenant scoping if organization_id provided)
                    query = select(CostFixed).where(CostFixed.name == row.get("name", ""))
                    if organization_id is not None:
                        query = query.where(CostFixed.organization_id == organization_id)
                    result = await db.execute(query)
                    existing = result.scalar_one_or_none()

                    sheet_currency = row_currency(row)

                    if existing:
                        # Update existing cost
                        existing.amount_monthly = float(row.get("amount_monthly", 0))
                        existing.category = row.get("category", "")
                        # Sólo pisa la moneda si la hoja declara una válida.
                        if sheet_currency:
                            existing.currency = sheet_currency
                    else:
                        # Create new cost (with tenant scoping)
                        new_cost = CostFixed(
                            name=row.get("name", ""),
                            amount_monthly=float(row.get("amount_monthly", 0)),
                            category=row.get("category", "general"),
                            organization_id=organization_id,  # Multi-tenant: assign to organization
                            currency=sheet_currency or default_currency,
                        )
                        db.add(new_cost)

                    records_synced += 1
                except Exception as e:
                    errors.append(f"Error syncing cost row: {str(e)}")

            await db.commit()

        except Exception as e:
            errors.append(f"Error syncing costs sheet: {str(e)}")

        # Sync Team Members (from "Team" sheet)
        try:
            team_sheet = spreadsheet.worksheet("Team")
            team_data = team_sheet.get_all_records()

            for row in team_data:
                try:
                    # Check if team member already exists (with tenant scoping if organization_id provided)
                    query = select(TeamMember).where(TeamMember.name == row.get("name", ""))
                    if organization_id is not None:
                        query = query.where(TeamMember.organization_id == organization_id)
                    result = await db.execute(query)
                    existing = result.scalar_one_or_none()

                    sheet_currency = row_currency(row)

                    if existing:
                        # Update existing member
                        existing.salary_monthly_brute = float(row.get("salary_monthly_brute", 0))
                        existing.billable_hours_per_week = float(
                            row.get("billable_hours_per_week", 40)
                        )
                        existing.role = row.get("role", "")
                        existing.is_active = row.get("is_active", True)
                        # Antes la moneda del miembro existente nunca se actualizaba:
                        # el sueldo viajaba de la hoja pero la unidad quedaba vieja.
                        if sheet_currency:
                            existing.currency = sheet_currency
                    else:
                        # Create new member (with tenant scoping)
                        # Note: user_id would need to be mapped from email if available
                        new_member = TeamMember(
                            name=row.get("name", ""),
                            salary_monthly_brute=float(row.get("salary_monthly_brute", 0)),
                            billable_hours_per_week=float(row.get("billable_hours_per_week", 40)),
                            role=row.get("role", ""),
                            apply_social_charges=True,
                            is_active=row.get("is_active", True),
                            organization_id=organization_id,  # Multi-tenant: assign to organization
                            currency=sheet_currency or default_currency,
                        )
                        db.add(new_member)

                    records_synced += 1
                except Exception as e:
                    errors.append(f"Error syncing team member row: {str(e)}")

            await db.commit()

        except Exception as e:
            errors.append(f"Error syncing team sheet: {str(e)}")

        return {
            "success": len(errors) == 0,
            "message": f"Synced {records_synced} records from Google Sheets",
            "records_synced": records_synced,
            "errors": errors,
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error syncing Google Sheets: {str(e)}",
            "records_synced": 0,
            "errors": [str(e)],
        }
