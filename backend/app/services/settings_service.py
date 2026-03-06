"""
Settings Service - Single point of access for organization and agency settings.
Unifies currency/country resolution and validation (core/currency remains the validator).
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.currency import get_currency_symbol, is_valid_currency
from app.core.logging import get_logger
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.settings_repository import SettingsRepository

logger = get_logger(__name__)


class SettingsService:
    """
    Service for reading/updating organization and agency settings.
    All access to organization.settings (e.g. primary_currency) should go through this service.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.org_repo = OrganizationRepository(db)
        self.settings_repo = SettingsRepository(db)

    async def get_primary_currency(self, organization_id: Optional[int] = None) -> str:
        """
        Get primary currency for the given organization or global default.

        Priority: organization.settings['primary_currency'] > AgencySettings.primary_currency > "USD".

        Args:
            organization_id: Organization ID; if None, returns global default only.

        Returns:
            Currency code (e.g. "USD").
        """
        if organization_id:
            org = await self.org_repo.get_by_id(organization_id)
            if org and isinstance(getattr(org, "settings", None), dict):
                # Backward-compat fallback: older tenants may still have only `currency`.
                primary = org.settings.get("primary_currency") or org.settings.get("currency")
                if primary and is_valid_currency(primary):
                    return primary
            # Tenant-safe default: do not inherit another tenant's global override.
            return "USD"
        default_settings = await self.settings_repo.get_or_create_default()
        return default_settings.primary_currency or "USD"

    async def get_organization_currency_and_social_config(
        self, organization_id: Optional[int] = None
    ) -> tuple[str, Optional[dict]]:
        """
        Get primary_currency and social_charges_config for an organization (e.g. for calculations).
        Single place for organization.settings access used by project/quote and onboarding flows.

        Returns:
            (primary_currency, social_charges_config or None)
        """
        primary_currency = await self.get_primary_currency(organization_id)
        social_config = None
        if organization_id:
            org = await self.org_repo.get_by_id(organization_id)
            if org and isinstance(getattr(org, "settings", None), dict):
                social_config = org.settings.get("social_charges_config")
        return primary_currency, social_config

    async def update_primary_currency(
        self,
        currency: str,
        organization_id: Optional[int] = None,
    ) -> None:
        """
        Update primary currency. Validates with is_valid_currency (single point of truth).

        Updates organization.settings when organization_id is set, and syncs global AgencySettings.

        Args:
            currency: New primary currency code.
            organization_id: If set, update this organization's settings; otherwise only global.
        """
        if not is_valid_currency(currency):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid currency: {currency}. Supported: USD, COP, ARS, EUR, PEN, MXN"
            )
        if organization_id:
            org = await self.org_repo.get_by_id(organization_id)
            if org:
                settings = org.settings if isinstance(getattr(org, "settings", None), dict) else {}
                settings = dict(settings)
                settings["primary_currency"] = currency
                org.settings = settings
                await self.db.commit()
                logger.info(
                    "Organization currency settings updated",
                    currency=currency,
                    org_id=organization_id,
                    module="settings_service",
                    function="update_primary_currency",
                )
        # Only update global defaults when this is a global operation.
        if not organization_id:
            default_settings = await self.settings_repo.get_or_create_default()
            default_settings.primary_currency = currency
            default_settings.currency_symbol = get_currency_symbol(currency)
            await self.settings_repo.update(default_settings)
