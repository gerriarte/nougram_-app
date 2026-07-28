"""
Settings Service - Single point of access for organization and agency settings.
Unifies currency/country resolution and validation (core/currency remains the validator).
"""

from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.currency import (
    DEFAULT_CURRENCY,
    EXCHANGE_RATES_TO_USD,
    get_currency_symbol,
    is_valid_currency,
    resolve_primary_currency,
)
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

    @staticmethod
    def _quantize(value: Decimal, scale: int) -> Decimal:
        return value.quantize(Decimal("1").scaleb(-scale), rounding=ROUND_HALF_UP)

    def _convert_decimal(
        self, amount: Decimal, from_currency: str, to_currency: str, scale: int
    ) -> Decimal:
        from_code = (from_currency or "USD").upper()
        to_code = (to_currency or "USD").upper()
        if from_code == to_code:
            return self._quantize(amount, scale)
        from_rate = EXCHANGE_RATES_TO_USD.get(from_code)
        to_rate = EXCHANGE_RATES_TO_USD.get(to_code)
        if from_rate is None or to_rate is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported currency conversion: {from_code} -> {to_code}",
            )
        converted = (amount / Decimal(str(from_rate))) * Decimal(str(to_rate))
        return self._quantize(converted, scale)

    async def _normalize_team_members_currency(
        self,
        organization_id: int,
        to_currency: str,
    ) -> int:
        from app.models.team import TeamMember

        result = await self.db.execute(
            select(TeamMember).where(TeamMember.organization_id == organization_id)
        )
        records = result.scalars().all()
        updated = 0
        for record in records:
            record_currency = (record.currency or "").upper()
            if record_currency == to_currency:
                continue
            if not is_valid_currency(record_currency):
                continue
            record.salary_monthly_brute = self._convert_decimal(
                Decimal(str(record.salary_monthly_brute)),
                record_currency,
                to_currency,
                scale=4,
            )
            record.currency = to_currency
            updated += 1
        return updated

    async def _normalize_fixed_costs_currency(
        self,
        organization_id: int,
        to_currency: str,
    ) -> int:
        from app.models.cost import CostFixed

        result = await self.db.execute(
            select(CostFixed).where(CostFixed.organization_id == organization_id)
        )
        records = result.scalars().all()
        updated = 0
        for record in records:
            record_currency = (record.currency or "").upper()
            if record_currency == to_currency:
                continue
            if not is_valid_currency(record_currency):
                continue
            record.amount_monthly = self._convert_decimal(
                Decimal(str(record.amount_monthly)),
                record_currency,
                to_currency,
                scale=4,
            )
            record.currency = to_currency
            updated += 1
        return updated

    async def _normalize_equipment_currency(
        self,
        organization_id: int,
        to_currency: str,
    ) -> int:
        from app.models.equipment import EquipmentAmortization

        result = await self.db.execute(
            select(EquipmentAmortization).where(
                EquipmentAmortization.organization_id == organization_id
            )
        )
        records = result.scalars().all()
        updated = 0
        for record in records:
            record_currency = (record.currency or "").upper()
            if record_currency == to_currency:
                continue
            if not is_valid_currency(record_currency):
                continue
            record.purchase_price = self._convert_decimal(
                Decimal(str(record.purchase_price)),
                record_currency,
                to_currency,
                scale=2,
            )
            record.salvage_value = self._convert_decimal(
                Decimal(str(record.salvage_value)),
                record_currency,
                to_currency,
                scale=2,
            )
            record.currency = to_currency
            record.exchange_rate_at_purchase = None
            updated += 1
        return updated

    async def _normalize_projects_quotes_currency(
        self,
        organization_id: int,
        to_currency: str,
    ) -> int:
        from app.models.project import Project, Quote

        result = await self.db.execute(
            select(Project)
            .options(
                selectinload(Project.quotes).selectinload(Quote.items),
                selectinload(Project.quotes).selectinload(Quote.expenses),
            )
            .where(Project.organization_id == organization_id)
        )
        projects = result.scalars().all()
        updated = 0

        for project in projects:
            if self._normalize_single_project_currency(project, to_currency):
                updated += 1

        return updated

    def _normalize_single_project_currency(self, project, to_currency: str) -> bool:
        """Convierte importes y reetiqueta UN proyecto (con sus quotes/ítems/expenses ya cargados)."""
        project_currency = (project.currency or "").upper()
        if project_currency == to_currency:
            return False
        if not is_valid_currency(project_currency):
            return False

        project.currency = to_currency

        for quote in project.quotes:
            if quote.total_internal_cost is not None:
                quote.total_internal_cost = self._convert_decimal(
                    Decimal(str(quote.total_internal_cost)),
                    project_currency,
                    to_currency,
                    scale=4,
                )
            if quote.total_client_price is not None:
                quote.total_client_price = self._convert_decimal(
                    Decimal(str(quote.total_client_price)),
                    project_currency,
                    to_currency,
                    scale=4,
                )
            if quote.revision_cost_per_additional is not None:
                quote.revision_cost_per_additional = self._convert_decimal(
                    Decimal(str(quote.revision_cost_per_additional)),
                    project_currency,
                    to_currency,
                    scale=4,
                )
            # El contingente porcentual no lleva moneda; el fijo sí.
            if (
                quote.contingency_value is not None
                and (quote.contingency_type or "").lower() == "fixed"
            ):
                quote.contingency_value = self._convert_decimal(
                    Decimal(str(quote.contingency_value)),
                    project_currency,
                    to_currency,
                    scale=4,
                )

            for item in quote.items:
                for attr in (
                    "internal_cost",
                    "client_price",
                    # El override manual de precio se aplica como último paso en
                    # calculations.py: si no se convierte, la próxima recalculación
                    # pisa la línea con el importe en la moneda vieja.
                    "client_price_override",
                    "fixed_price",
                    "recurring_price",
                    "project_value",
                ):
                    value = getattr(item, attr, None)
                    if value is None:
                        continue
                    setattr(
                        item,
                        attr,
                        self._convert_decimal(
                            Decimal(str(value)),
                            project_currency,
                            to_currency,
                            scale=4,
                        ),
                    )

            for expense in quote.expenses:
                if expense.cost is not None:
                    expense.cost = self._convert_decimal(
                        Decimal(str(expense.cost)),
                        project_currency,
                        to_currency,
                        scale=4,
                    )
                if expense.client_price is not None:
                    expense.client_price = self._convert_decimal(
                        Decimal(str(expense.client_price)),
                        project_currency,
                        to_currency,
                        scale=4,
                    )

        return True

    async def normalize_project_currency(self, project_id: int, to_currency: str) -> str | None:
        """
        Convierte y reetiqueta UN proyecto a `to_currency`.

        Los endpoints de presupuesto reetiquetaban project.currency con la moneda primaria
        SIN convertir un solo importe, así que las versiones ya guardadas (y sus PDFs y
        mails) pasaban a leerse con la etiqueta nueva sobre números viejos. Este método es
        la pieza que faltaba: hace la conversión antes del reetiquetado.

        No commitea: el endpoint que lo llama cierra la transacción.

        Returns:
            La moneda anterior del proyecto si hubo conversión; None si no hizo falta.
        """
        from app.models.project import Project, Quote

        if not is_valid_currency(to_currency):
            return None

        result = await self.db.execute(
            select(Project)
            .options(
                selectinload(Project.quotes).selectinload(Quote.items),
                selectinload(Project.quotes).selectinload(Quote.expenses),
            )
            .where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if project is None:
            return None

        previous_currency = (project.currency or "").upper()
        if not self._normalize_single_project_currency(project, to_currency.upper()):
            # Sin conversión posible: al menos que la etiqueta no mienta más de lo que ya miente.
            if previous_currency != to_currency.upper() and not is_valid_currency(
                previous_currency
            ):
                project.currency = to_currency.upper()
            return None

        logger.info(
            "Project currency normalized before quote recalculation",
            project_id=project_id,
            from_currency=previous_currency,
            to_currency=to_currency.upper(),
            module="settings_service",
            function="normalize_project_currency",
        )
        return previous_currency

    def convert_quote_payload_amounts(
        self,
        quote_data,
        from_currency: str,
        to_currency: str,
    ) -> bool:
        """
        Convierte los importes tipeados a mano que llegan en el payload de un presupuesto.

        La UI muestra los precios en project.currency; si la org ya cotiza en otra moneda,
        guardar sin tocar nada reenvía esos mismos números y quedaban almacenados con la
        etiqueta nueva (5.000 USD guardados como 5.000 COP). Los ítems por hora se
        recalculan con el BCR, pero fixed/recurring/project_value/override son literales.

        Muta `quote_data` in place. Devuelve True si hubo alguna conversión.
        """
        from_code = (from_currency or "").upper()
        to_code = (to_currency or "").upper()
        if not from_code or from_code == to_code:
            return False
        if not is_valid_currency(from_code) or not is_valid_currency(to_code):
            return False

        def _convert(value):
            if value is None:
                return None
            return self._convert_decimal(Decimal(str(value)), from_code, to_code, scale=4)

        for item in getattr(quote_data, "items", None) or []:
            for attr in (
                "fixed_price",
                "recurring_price",
                "project_value",
                "client_price_override",
            ):
                value = getattr(item, attr, None)
                if value is not None:
                    setattr(item, attr, _convert(value))

        for expense in getattr(quote_data, "expenses", None) or []:
            if getattr(expense, "cost", None) is not None:
                expense.cost = _convert(expense.cost)

        if getattr(quote_data, "revision_cost_per_additional", None) is not None:
            quote_data.revision_cost_per_additional = _convert(
                quote_data.revision_cost_per_additional
            )

        if (
            getattr(quote_data, "contingency_value", None) is not None
            and str(getattr(quote_data, "contingency_type", "") or "").lower() == "fixed"
        ):
            quote_data.contingency_value = _convert(quote_data.contingency_value)

        return True

    async def _normalize_operational_currency_for_organization(
        self,
        organization_id: int,
        to_currency: str,
    ) -> dict[str, int]:
        return {
            "team_members": await self._normalize_team_members_currency(
                organization_id, to_currency
            ),
            "fixed_costs": await self._normalize_fixed_costs_currency(organization_id, to_currency),
            "equipment": await self._normalize_equipment_currency(organization_id, to_currency),
            "projects": await self._normalize_projects_quotes_currency(
                organization_id, to_currency
            ),
        }

    async def get_primary_currency(self, organization_id: int | None = None) -> str:
        """
        Get primary currency for the given organization or global default.

        Organization-scoped resolution is delegated to resolve_primary_currency()
        (app/core/currency.py), the single canonical resolver: primary_currency >
        currency > template_applied_currency > country default > "USD".

        Args:
            organization_id: Organization ID; if None, returns global default only.

        Returns:
            Currency code (e.g. "USD").
        """
        if organization_id:
            org = await self.org_repo.get_by_id(organization_id)
            # Tenant-safe: the resolver never inherits another tenant's global override.
            return resolve_primary_currency(org)
        default_settings = await self.settings_repo.get_or_create_default()
        return default_settings.primary_currency or DEFAULT_CURRENCY

    async def get_organization_currency_and_social_config(
        self, organization_id: int | None = None
    ) -> tuple[str, dict | None]:
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
        organization_id: int | None = None,
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
                detail=f"Invalid currency: {currency}. Supported: USD, COP, ARS, EUR, PEN, MXN",
            )
        target_currency = currency.upper()
        if organization_id:
            org = await self.org_repo.get_by_id(organization_id)
            if org:
                settings = org.settings if isinstance(getattr(org, "settings", None), dict) else {}
                settings = dict(settings)
                previous_currency = resolve_primary_currency(settings)
                settings["primary_currency"] = target_currency
                settings["currency"] = target_currency
                org.settings = settings

                # resolve_primary_currency() ya garantiza un código válido.
                migration_summary = await self._normalize_operational_currency_for_organization(
                    organization_id=organization_id,
                    to_currency=target_currency,
                )

                await self.db.commit()
                logger.info(
                    "Organization currency settings updated with automatic normalization",
                    from_currency=previous_currency,
                    to_currency=target_currency,
                    migration_summary=migration_summary,
                    org_id=organization_id,
                    module="settings_service",
                    function="update_primary_currency",
                )
        # Only update global defaults when this is a global operation.
        if not organization_id:
            default_settings = await self.settings_repo.get_or_create_default()
            default_settings.primary_currency = target_currency
            default_settings.currency_symbol = get_currency_symbol(target_currency)
            await self.settings_repo.update(default_settings)
