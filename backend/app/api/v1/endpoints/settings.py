"""
Agency settings endpoints (thin layer: auth + SettingsService + response).
Currency/country validation and organization.settings access are in SettingsService.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.currency import get_all_currencies, get_currency_symbol
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.permissions import get_user_role
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.settings import (
    AgencySettingsResponse,
    AgencySettingsUpdate,
    ExchangeRatesResponse,
    FeatureFlagsResponse,
)
from app.services.exchange_rate_service import get_today_exchange_rates
from app.services.settings_service import SettingsService

logger = get_logger(__name__)

router = APIRouter()


@router.get("/features", response_model=FeatureFlagsResponse)
async def get_feature_flags(
    current_user: User = Depends(get_current_user),
):
    """
    Return frontend feature flags for resource planning modules.

    Occupancy tracking remains enabled in all modes; team cells can be toggled
    independently to support simple/advanced experiences per environment.
    """
    _ = current_user  # Keep authenticated access for tenant-facing settings endpoints.
    team_cells_enabled = bool(settings.FEATURE_TEAM_CELLS)
    return FeatureFlagsResponse(
        team_cells_enabled=team_cells_enabled,
        resource_occupancy_enabled=True,
        resource_planning_mode="advanced" if team_cells_enabled else "simple",
    )


@router.get("/currency", response_model=AgencySettingsResponse)
async def get_agency_currency_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    include_rates: bool = False,
):
    """
    Get agency currency settings
    Returns the primary currency and available currencies.

    If include_rates=true and user is owner or super_admin, also returns today's exchange rates.
    """
    try:
        settings_service = SettingsService(db)
        primary_currency = await settings_service.get_primary_currency(current_user.organization_id)

        user_role = get_user_role(current_user)
        can_view_rates = user_role in ["owner", "super_admin"]
        exchange_rates = None
        if include_rates and can_view_rates:
            try:
                exchange_rates = await get_today_exchange_rates()
            except Exception as e:
                logger.warning(
                    "Error fetching exchange rates", error=str(e), user_id=current_user.id
                )

        return AgencySettingsResponse(
            primary_currency=primary_currency,
            currency_symbol=get_currency_symbol(primary_currency),
            available_currencies=get_all_currencies(),
            exchange_rates=exchange_rates,
        )
    except Exception as e:
        logger.error(
            "Error getting currency settings", error=str(e), user_id=current_user.id, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting currency settings: {str(e)}",
        )


@router.put("/currency", response_model=AgencySettingsResponse)
async def update_agency_currency_settings(
    settings_data: AgencySettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update agency primary currency settings

    This affects how costs and prices are displayed and calculated.
    Validation (is_valid_currency) is done in SettingsService.
    """
    try:
        settings_service = SettingsService(db)
        await settings_service.update_primary_currency(
            settings_data.primary_currency,
            organization_id=current_user.organization_id,
        )
        logger.info("Currency settings updated successfully", user_id=current_user.id)
        return AgencySettingsResponse(
            primary_currency=settings_data.primary_currency,
            currency_symbol=get_currency_symbol(settings_data.primary_currency),
            available_currencies=get_all_currencies(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error updating currency settings", error=str(e), user_id=current_user.id, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating currency settings: {str(e)}",
        )


@router.get("/currency/exchange-rates", response_model=ExchangeRatesResponse)
async def get_exchange_rates(
    current_user: User = Depends(get_current_user),
):
    """
    Get today's exchange rates for all supported currencies.

    Only available for owner and super_admin roles.
    """
    try:
        # Check permissions
        user_role = get_user_role(current_user)
        if user_role not in ["owner", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners and super admins can view exchange rates",
            )

        rates = await get_today_exchange_rates()

        return ExchangeRatesResponse(rates=rates, base_currency="USD")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting exchange rates", error=str(e), user_id=current_user.id, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting exchange rates: {str(e)}",
        )
