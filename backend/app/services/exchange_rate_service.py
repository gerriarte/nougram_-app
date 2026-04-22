"""
Exchange rate service for fetching real-time currency exchange rates
"""

from datetime import datetime, timedelta
from typing import Any

import httpx

from app.core.config import settings
from app.core.currency import CURRENCY_INFO, EXCHANGE_RATES_TO_USD
from app.core.logging import get_logger

logger = get_logger(__name__)

# Cache for exchange rates (valid for 24 hours - daily rates)
_exchange_rate_cache: dict[str, any] | None = None
_cache_timestamp: datetime | None = None
CACHE_DURATION = timedelta(hours=24)  # Daily rates - update once per day


async def get_exchange_rates(base_currency: str = "USD") -> dict[str, float]:
    """
    Get current exchange rates from API or cache

    Args:
        base_currency: Base currency code (default: USD)

    Returns:
        Dictionary mapping currency codes to exchange rates relative to base currency
    """
    global _exchange_rate_cache, _cache_timestamp

    # Check cache validity
    if _exchange_rate_cache and _cache_timestamp:
        if datetime.now() - _cache_timestamp < CACHE_DURATION:
            logger.debug("Returning cached exchange rates", base_currency=base_currency)
            return _exchange_rate_cache

    # Fetch from API
    try:
        if settings.EXCHANGE_RATE_API_KEY:
            # Use API key if available (for paid tier)
            url = f"https://v6.exchangerate-api.com/v6/{settings.EXCHANGE_RATE_API_KEY}/latest/{base_currency}"
        else:
            # Use free tier endpoint (no API key required)
            url = f"{settings.EXCHANGE_RATE_API_URL}/{base_currency}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            # Extract rates from response
            if "rates" in data:
                rates = data["rates"]
            elif "conversion_rates" in data:
                rates = data["conversion_rates"]
            else:
                # Fallback to default rates if API response format is unexpected
                logger.warning("Unexpected API response format, using default rates")
                return EXCHANGE_RATES_TO_USD.copy()

            # Update cache
            _exchange_rate_cache = rates
            _cache_timestamp = datetime.now()

            logger.info(
                "Fetched daily exchange rates from API",
                base_currency=base_currency,
                rates_count=len(rates),
            )
            return rates

    except httpx.HTTPError as e:
        logger.error(
            "Error fetching exchange rates from API", error=str(e), base_currency=base_currency
        )
        # Fallback to default rates
        return EXCHANGE_RATES_TO_USD.copy()
    except Exception as e:
        logger.error(
            "Unexpected error fetching exchange rates",
            error=str(e),
            base_currency=base_currency,
            exc_info=True,
        )
        # Fallback to default rates
        return EXCHANGE_RATES_TO_USD.copy()


async def get_exchange_rate_to_usd(currency: str) -> float:
    """
    Get exchange rate for a currency relative to USD

    Args:
        currency: Currency code

    Returns:
        Exchange rate (1 USD = X currency)
    """
    if currency == "USD":
        return 1.0

    rates = await get_exchange_rates("USD")
    rate = rates.get(currency)

    if rate is None:
        logger.warning("Exchange rate not found for currency, using default", currency=currency)
        return EXCHANGE_RATES_TO_USD.get(currency, 1.0)

    return rate


async def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """
    Get exchange rate between two currencies

    Args:
        from_currency: Source currency code
        to_currency: Target currency code

    Returns:
        Exchange rate (1 from_currency = X to_currency)
    """
    if from_currency == to_currency:
        return 1.0

    # Get rates relative to USD
    rates = await get_exchange_rates("USD")

    from_rate = rates.get(from_currency, EXCHANGE_RATES_TO_USD.get(from_currency, 1.0))
    to_rate = rates.get(to_currency, EXCHANGE_RATES_TO_USD.get(to_currency, 1.0))

    # Convert: 1 from_currency = (1/from_rate) USD = (1/from_rate) * to_rate to_currency
    if from_currency == "USD":
        return to_rate
    elif to_currency == "USD":
        return 1.0 / from_rate
    else:
        return to_rate / from_rate


async def get_today_exchange_rates() -> dict[str, dict[str, Any]]:
    """
    Get today's exchange rates for all supported currencies relative to USD

    Returns:
        Dictionary with currency codes as keys and exchange rate info as values
        Example: {
            "COP": {
                "rate": 4000.0,
                "rate_to_usd": 4000.0,
                "last_updated": "2024-01-01T12:00:00Z"
            }
        }
    """
    rates = await get_exchange_rates("USD")

    result = {}
    for currency_code in CURRENCY_INFO.keys():
        if currency_code == "USD":
            result[currency_code] = {
                "rate": 1.0,
                "rate_to_usd": 1.0,
                "last_updated": _cache_timestamp.isoformat()
                if _cache_timestamp
                else datetime.now().isoformat(),
            }
        else:
            rate = rates.get(currency_code, EXCHANGE_RATES_TO_USD.get(currency_code, 1.0))
            result[currency_code] = {
                "rate": rate,
                "rate_to_usd": rate,
                "last_updated": _cache_timestamp.isoformat()
                if _cache_timestamp
                else datetime.now().isoformat(),
            }

    return result
