"""
Pydantic schemas for Agency Settings
ESTÁNDAR NOUGRAM: Campos monetarios y tasas usan Decimal serializado como string
"""
from typing import Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, field_serializer
from app.core.currency import Currency
from app.core.pydantic_config import DECIMAL_CONFIG


class AgencySettingsResponse(BaseModel):
    """Schema for agency settings response"""
    primary_currency: str = Field(..., description="Primary currency code (USD, COP, ARS, EUR, PEN)")
    currency_symbol: str = Field(..., description="Currency symbol")
    available_currencies: list[dict] = Field(default_factory=list, description="List of available currencies")
    exchange_rates: Optional[Dict[str, Any]] = Field(None, description="Today's exchange rates (only for owner/super_admin)")

    class Config:
        from_attributes = True


class AgencySettingsUpdate(BaseModel):
    """Schema for updating agency settings"""
    primary_currency: str = Field(..., description="Primary currency code (USD, COP, ARS, EUR, PEN)")


class ExchangeRateInfo(BaseModel):
    """Schema for exchange rate information
    ESTÁNDAR NOUGRAM: Tasas de cambio usan Decimal para precisión
    """
    rate: Decimal = Field(..., description="Exchange rate to USD")
    rate_to_usd: Decimal = Field(..., description="Exchange rate to USD (same as rate)")
    last_updated: str = Field(..., description="ISO timestamp of last update")
    
    # ESTÁNDAR NOUGRAM: Serializar Decimal como string
    @field_serializer('rate', 'rate_to_usd')
    def serialize_decimal(self, value: Decimal) -> str:
        """Serializa Decimal como string para mantener precisión"""
        return str(value) if value is not None else None
    
    model_config = DECIMAL_CONFIG


class ExchangeRatesResponse(BaseModel):
    """Schema for exchange rates response"""
    rates: Dict[str, ExchangeRateInfo] = Field(..., description="Exchange rates for all supported currencies")
    base_currency: str = Field(default="USD", description="Base currency for rates")
