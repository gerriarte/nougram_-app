"""
Currency utilities and constants
ESTÁNDAR NOUGRAM: Usa Money para precisión en formateo y conversiones
"""
import math
from decimal import Decimal
from enum import Enum
from typing import Any

from app.core.money import Money


class Currency(str, Enum):
    """Supported currencies"""
    USD = "USD"  # US Dollar
    COP = "COP"  # Colombian Peso
    ARS = "ARS"  # Argentine Peso
    EUR = "EUR"  # Euro
    PEN = "PEN"  # Peruvian Sol
    MXN = "MXN"  # Mexican Peso


CURRENCY_INFO: dict[str, dict[str, Any]] = {
    "USD": {
        "symbol": "$",
        "name": "US Dollar",
        "locale": "en-US",
        "decimal_places": 2,
        "thousands_separator": ",",  # Thousands separator
        "decimal_separator": ".",  # Decimal separator
        "grouping": 3,  # Group digits by 3 (thousands, millions, etc.)
    },
    "COP": {
        "symbol": "$",
        "name": "Colombian Peso",
        "locale": "es-CO",
        "decimal_places": 0,  # COP typically doesn't use decimals
        "thousands_separator": ".",  # Thousands separator (period in Spanish)
        "decimal_separator": ",",  # Decimal separator (comma in Spanish)
        "grouping": 3,  # Group digits by 3 (thousands, millions, etc.)
    },
    "ARS": {
        "symbol": "$",
        "name": "Argentine Peso",
        "locale": "es-AR",
        "decimal_places": 2,
        "thousands_separator": ".",  # Thousands separator
        "decimal_separator": ",",  # Decimal separator
        "grouping": 3,  # Group digits by 3 (thousands, millions, etc.)
    },
    "EUR": {
        "symbol": "€",
        "name": "Euro",
        "locale": "en-EU",
        "decimal_places": 2,
        "thousands_separator": ".",  # Thousands separator
        "decimal_separator": ",",  # Decimal separator
        "grouping": 3,  # Group digits by 3 (thousands, millions, etc.)
    },
    "PEN": {
        "symbol": "S/",
        "name": "Peruvian Sol",
        "locale": "es-PE",
        "decimal_places": 2,
        "thousands_separator": ",",
        "decimal_separator": ".",
        "grouping": 3,
    },
    "MXN": {
        "symbol": "$",
        "name": "Mexican Peso",
        "locale": "es-MX",
        "decimal_places": 2,
        "thousands_separator": ",",
        "decimal_separator": ".",
        "grouping": 3,
    },
}

# Exchange rates to USD (base currency)
# NOTE: These are example rates. In production, you should fetch real-time rates
# from an API like exchangerate-api.com, fixer.io, or similar
EXCHANGE_RATES_TO_USD: dict[str, float] = {
    "USD": 1.0,      # Base currency
    "COP": 4000.0,   # Example: 1 USD = 4000 COP (update with real rates)
    "ARS": 850.0,    # Example: 1 USD = 850 ARS (update with real rates)
    "EUR": 0.92,     # Example: 1 USD = 0.92 EUR (update with real rates)
    "PEN": 3.7,      # Example: 1 USD = 3.7 PEN (update with real rates)
    "MXN": 17.0,     # Example: 1 USD = 17.0 MXN (update with real rates)
}


def format_currency(
    amount: float | Decimal | Money,
    currency: str = "USD",
    use_grouping: bool = True
) -> str:
    """
    Format amount as currency string with proper thousands/millions grouping
    ESTÁNDAR NOUGRAM: Acepta Money, Decimal o float para compatibilidad
    
    Args:
        amount: Amount to format (Money, Decimal, or float)
        currency: Currency code (USD, COP, ARS, EUR, PEN, MXN). Si amount es Money, se usa su currency
        use_grouping: Whether to use thousands/millions grouping (default: True)
        
    Returns:
        Formatted currency string (e.g., "$ 1.000.000" for COP, "$ 1,000,000.00" for USD)
    """
    # ESTÁNDAR NOUGRAM: Si es Money, usar su currency y quantizar
    if isinstance(amount, Money):
        currency = amount.currency
        # Quantizar según la moneda
        if currency == "COP":
            quantized = amount.quantize()
        else:
            quantized = amount.quantize()
        amount_decimal = quantized.amount
    elif isinstance(amount, Decimal):
        amount_decimal = amount
    else:
        # Compatibilidad hacia atrás: convertir float a Decimal
        amount_decimal = Decimal(str(amount))
    
    currency_info = CURRENCY_INFO.get(currency, CURRENCY_INFO["USD"])
    symbol = currency_info.get("symbol", "$")
    decimal_places = currency_info.get("decimal_places", 2)
    thousands_sep = currency_info.get("thousands_separator", ",")
    decimal_sep = currency_info.get("decimal_separator", ".")
    grouping = currency_info.get("grouping", 3)
    
    # ESTÁNDAR NOUGRAM: Redondear usando Decimal para precisión
    precision = Decimal('1') if decimal_places == 0 else Decimal('0.1') ** decimal_places
    rounded_decimal = amount_decimal.quantize(precision)
    
    # Convertir a float solo para formateo (ya está redondeado)
    rounded_amount = float(rounded_decimal)
    
    # Split into integer and decimal parts
    integer_part = int(abs(rounded_amount))
    decimal_part = abs(rounded_amount) - integer_part
    
    # Format integer part with grouping
    if use_grouping and grouping > 0:
        integer_str = str(integer_part)
        # Reverse string to group from right to left
        reversed_str = integer_str[::-1]
        grouped_parts = []
        for i in range(0, len(reversed_str), grouping):
            grouped_parts.append(reversed_str[i:i+grouping])
        grouped_str = thousands_sep.join(grouped_parts)
        integer_str = grouped_str[::-1]
    else:
        integer_str = str(integer_part)
    
    # Format decimal part
    if decimal_places > 0 and decimal_part > 0:
        decimal_str = f"{decimal_part:.{decimal_places}f}"[2:]  # Remove "0."
        formatted_amount = f"{integer_str}{decimal_sep}{decimal_str}"
    else:
        formatted_amount = integer_str
    
    # Add negative sign if needed
    if rounded_amount < 0:
        formatted_amount = f"-{formatted_amount}"
    
    # Add currency symbol
    return f"{symbol} {formatted_amount}"


def get_currency_symbol(currency: str = "USD") -> str:
    """
    Get currency symbol
    
    Args:
        currency: Currency code
        
    Returns:
        Currency symbol
    """
    return CURRENCY_INFO.get(currency, CURRENCY_INFO["USD"]).get("symbol", "$")


def get_currency_name(currency: str = "USD") -> str:
    """
    Get currency name
    
    Args:
        currency: Currency code
        
    Returns:
        Currency name
    """
    return CURRENCY_INFO.get(currency, CURRENCY_INFO["USD"]).get("name", "US Dollar")


def is_valid_currency(currency: str) -> bool:
    """
    Check if currency code is valid
    
    Args:
        currency: Currency code to validate
        
    Returns:
        True if valid, False otherwise
    """
    return currency in CURRENCY_INFO


def get_all_currencies() -> list[dict[str, str]]:
    """
    Get list of all supported currencies
    
    Returns:
        List of currency dictionaries with code, symbol, and name
    """
    return [
        {
            "code": code,
            "symbol": info["symbol"],
            "name": info["name"],
        }
        for code, info in CURRENCY_INFO.items()
    ]


def convert_currency(
    amount: float | Decimal | Money,
    from_currency: str,
    to_currency: str
) -> float | Money:
    """
    Convert amount from one currency to another
    ESTÁNDAR NOUGRAM: Usa Money para precisión en conversiones
    
    Args:
        amount: Amount to convert (Money, Decimal, or float)
        from_currency: Source currency code. Si amount es Money, se usa su currency
        to_currency: Target currency code
        
    Returns:
        Converted amount (Money si input es Money, float para compatibilidad)
    """
    # ESTÁNDAR NOUGRAM: Si es Money, usar su currency
    is_money = isinstance(amount, Money)
    if is_money:
        from_currency = amount.currency
        amount_decimal = amount.amount
    elif isinstance(amount, Decimal):
        amount_decimal = amount
    else:
        amount_decimal = Decimal(str(amount))
    
    if from_currency == to_currency:
        if is_money:
            return amount
        return float(amount_decimal)
    
    # ESTÁNDAR NOUGRAM: Convertir usando Decimal para precisión
    # Convert to USD first (base currency)
    from_rate = Decimal(str(EXCHANGE_RATES_TO_USD.get(from_currency, 1.0)))
    amount_in_usd = amount_decimal / from_rate
    
    # Convert from USD to target currency
    to_rate = Decimal(str(EXCHANGE_RATES_TO_USD.get(to_currency, 1.0)))
    converted_decimal = amount_in_usd * to_rate
    
    # Retornar Money si input era Money, float para compatibilidad
    if is_money:
        return Money(converted_decimal, to_currency)
    return float(converted_decimal)


def normalize_to_primary_currency(
    amount: float | Decimal | Money,
    from_currency: str | None,
    primary_currency: str = "USD"
) -> float | Money:
    """
    Normalize amount to primary currency
    ESTÁNDAR NOUGRAM: Usa Money para precisión en normalización
    
    This is used for calculations where all costs need to be in the same currency.
    
    Args:
        amount: Amount to normalize (Money, Decimal, or float)
        from_currency: Source currency code (can be None, defaults to USD). Si amount es Money, se ignora
        primary_currency: Target primary currency code (default: USD)
        
    Returns:
        Normalized amount in primary currency (Money si input es Money, float para compatibilidad)
    """
    # ESTÁNDAR NOUGRAM: Si es Money, usar su currency
    is_money = isinstance(amount, Money)
    if is_money:
        from_currency = amount.currency
    
    # Handle None or empty currency
    if not from_currency or from_currency not in CURRENCY_INFO:
        from_currency = "USD"
    
    if not primary_currency or primary_currency not in CURRENCY_INFO:
        primary_currency = "USD"
    
    return convert_currency(amount, from_currency, primary_currency)
