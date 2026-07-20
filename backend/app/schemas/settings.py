"""
Pydantic schemas for Agency Settings
ESTÁNDAR NOUGRAM: Campos monetarios y tasas usan Decimal serializado como string
"""

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, field_serializer

from app.core.pydantic_config import DECIMAL_CONFIG


class AgencySettingsResponse(BaseModel):
    """Schema for agency settings response"""

    primary_currency: str = Field(
        ..., description="Primary currency code (USD, COP, ARS, EUR, PEN, MXN)"
    )
    currency_symbol: str = Field(..., description="Currency symbol")
    available_currencies: list[dict] = Field(
        default_factory=list, description="List of available currencies"
    )
    exchange_rates: dict[str, Any] | None = Field(
        None, description="Today's exchange rates (only for owner/super_admin)"
    )

    class Config:
        from_attributes = True


class AgencySettingsUpdate(BaseModel):
    """Schema for updating agency settings"""

    primary_currency: str = Field(
        ..., description="Primary currency code (USD, COP, ARS, EUR, PEN, MXN)"
    )


class ExchangeRateInfo(BaseModel):
    """Schema for exchange rate information
    ESTÁNDAR NOUGRAM: Tasas de cambio usan Decimal para precisión
    """

    rate: Decimal = Field(..., description="Exchange rate to USD")
    rate_to_usd: Decimal = Field(..., description="Exchange rate to USD (same as rate)")
    last_updated: str = Field(..., description="ISO timestamp of last update")

    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer("rate", "rate_to_usd")
    def serialize_decimal(self, value: Decimal) -> str:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None

    model_config = DECIMAL_CONFIG


class ExchangeRatesResponse(BaseModel):
    """Schema for exchange rates response"""

    rates: dict[str, ExchangeRateInfo] = Field(
        ..., description="Exchange rates for all supported currencies"
    )
    base_currency: str = Field(default="USD", description="Base currency for rates")


class FeatureFlagsResponse(BaseModel):
    """Schema for feature flags consumed by frontend modules."""

    team_cells_enabled: bool = Field(default=False, description="Enable advanced team cells module")
    resource_occupancy_enabled: bool = Field(
        default=True, description="Enable occupancy tracking regardless of planning mode"
    )
    resource_planning_mode: Literal["simple", "advanced"] = Field(
        default="simple", description="Planning mode for resource assignment UI"
    )
    quote_agent_enabled: bool = Field(
        default=False, description="Enable the AI quote agent (chat) module for this tenant"
    )
