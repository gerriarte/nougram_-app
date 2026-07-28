"""
Currency utilities and constants
ESTÁNDAR NOUGRAM: Usa Money para precisión en formateo y conversiones
"""

from collections.abc import Mapping
from decimal import Decimal
from enum import StrEnum
from typing import Any

from app.core.config import DEFAULT_EXCHANGE_RATES_TO_USD, parse_exchange_rate
from app.core.config import settings as app_settings
from app.core.logging import get_logger
from app.core.money import Money

logger = get_logger(__name__)

# Last-resort currency when nothing can be resolved. Kept as a named constant so
# the fallback is greppable instead of a magic "USD" scattered around the code.
DEFAULT_CURRENCY = "USD"


class Currency(StrEnum):
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

# Default currency per country/region code. Used only as a derivation step when an
# organization never persisted its primary currency (see resolve_primary_currency).
# Keys accept the ISO-2, ISO-3 and template "region" codes used across the product.
COUNTRY_DEFAULT_CURRENCY: dict[str, str] = {
    "CO": "COP",
    "COL": "COP",
    "COLOMBIA": "COP",
    "AR": "ARS",
    "ARG": "ARS",
    "ARGENTINA": "ARS",
    "MX": "MXN",
    "MEX": "MXN",
    "MEXICO": "MXN",
    "PE": "PEN",
    "PER": "PEN",
    "PERU": "PEN",
    "ES": "EUR",
    "ESP": "EUR",
    "SPAIN": "EUR",
    "EU": "EUR",
    "US": "USD",
    "USA": "USD",
}

# --- Exchange rates -----------------------------------------------------------
# Rates are STATIC and configurable per environment (app/core/config.py); no
# external rate API is called from here. Two audit fields travel with them:
#   EXCHANGE_RATES_AS_OF   -> date the rates were taken
#   EXCHANGE_RATES_SOURCE  -> where they came from ("placeholder:*" = not real data)
EXCHANGE_RATES_AS_OF: str = app_settings.EXCHANGE_RATES_AS_OF
EXCHANGE_RATES_SOURCE: str = app_settings.EXCHANGE_RATES_SOURCE
EXCHANGE_RATES_ARE_PLACEHOLDER: bool = app_settings.exchange_rates_are_placeholder


def _build_rates_to_usd(raw_rates: Mapping[str, Any]) -> dict[str, Decimal]:
    """
    Build the effective rate table, dropping anything that is not a finite Decimal > 0.

    The defaults are always the floor: a rejected override falls back to its default
    instead of disappearing. Without this, a single bad env var (e.g.
    EXCHANGE_RATES_TO_USD='{"COP": "4.150,00"}') raised InvalidOperation while this
    module was being imported and the whole app failed to boot; '{"COP": "0"}'
    booted fine and then blew up with DivisionByZero on the first conversion.
    """
    rates: dict[str, Decimal] = {}
    for code, value in DEFAULT_EXCHANGE_RATES_TO_USD.items():
        parsed = parse_exchange_rate(code, value)
        if parsed is not None:
            rates[code.strip().upper()] = parsed
    for code, value in raw_rates.items():
        parsed = parse_exchange_rate(code, value)
        if parsed is None:
            continue
        rates[str(code).strip().upper()] = parsed
    return rates


# ESTÁNDAR NOUGRAM: la fuente de verdad es Decimal; el dict float se mantiene solo
# por compatibilidad con call sites legacy que hacen Decimal(str(rate)).
EXCHANGE_RATES_TO_USD_DECIMAL: dict[str, Decimal] = _build_rates_to_usd(
    app_settings.exchange_rates_to_usd_dict
)
EXCHANGE_RATES_TO_USD: dict[str, float] = {
    code: float(rate) for code, rate in EXCHANGE_RATES_TO_USD_DECIMAL.items()
}

# Pairs already warned about, so a placeholder-rate conversion logs once per pair
# instead of once per row of every report.
_WARNED_PLACEHOLDER_PAIRS: set[tuple[str, str]] = set()

# Same idea for currency codes we have no rate for: warn once per code instead of
# once per row, so "no rate" stops being indistinguishable from a real 1:1 parity.
_WARNED_UNKNOWN_CURRENCIES: set[str] = set()


def _warn_unknown_currency(currency: str, function: str) -> None:
    """Warn once per unknown currency code (deduplicated for the process lifetime)."""
    code = (currency or "").strip().upper() or "<empty>"
    if code in _WARNED_UNKNOWN_CURRENCIES:
        return
    _WARNED_UNKNOWN_CURRENCIES.add(code)
    logger.warning(
        "Unsupported currency code: no exchange rate for it, so the amount is left "
        "untouched (implicit 1:1 parity with the default currency).",
        currency=code,
        fallback_currency=DEFAULT_CURRENCY,
        known_currencies=sorted(EXCHANGE_RATES_TO_USD_DECIMAL),
        module="currency",
        function=function,
    )


def get_exchange_rate_to_usd(currency: str) -> Decimal:
    """
    Rate for `currency` expressed as units per 1 USD.

    Returns Decimal("1") for unknown codes (treated as already-USD) to preserve the
    historical, non-raising behaviour of the conversion helpers — but logs a warning
    once per unknown code, because a missing rate and a genuine 1:1 parity produce
    the same number and used to be indistinguishable in the logs.
    """
    code = (currency or "").upper()
    rate = EXCHANGE_RATES_TO_USD_DECIMAL.get(code)
    if rate is None:
        _warn_unknown_currency(code, "get_exchange_rate_to_usd")
        return Decimal("1")
    return rate


def get_exchange_rates_metadata() -> dict[str, Any]:
    """
    Audit metadata for the rates currently in effect.

    Exposed so any converted amount can be traced back to the rate vintage and
    origin that produced it.
    """
    return {
        "as_of": EXCHANGE_RATES_AS_OF,
        "source": EXCHANGE_RATES_SOURCE,
        "is_placeholder": EXCHANGE_RATES_ARE_PLACEHOLDER,
        "rates_to_usd": {code: str(rate) for code, rate in EXCHANGE_RATES_TO_USD_DECIMAL.items()},
    }


def _warn_placeholder_conversion(from_currency: str, to_currency: str) -> None:
    """Warn once per currency pair when a real conversion uses placeholder rates."""
    if not EXCHANGE_RATES_ARE_PLACEHOLDER:
        return
    pair = (from_currency, to_currency)
    if pair in _WARNED_PLACEHOLDER_PAIRS:
        return
    _WARNED_PLACEHOLDER_PAIRS.add(pair)
    logger.warning(
        "Cross-currency conversion using placeholder exchange rates",
        from_currency=from_currency,
        to_currency=to_currency,
        rates_as_of=EXCHANGE_RATES_AS_OF,
        rates_source=EXCHANGE_RATES_SOURCE,
        module="currency",
        function="convert_currency",
    )


def _coerce_currency_code(value: Any) -> str | None:
    """Normalize a settings value (str, Currency enum, None) to a valid code or None."""
    raw = getattr(value, "value", value)
    if not isinstance(raw, str):
        return None
    code = raw.strip().upper()
    if not code or code not in CURRENCY_INFO:
        return None
    return code


def _extract_org_settings(org: Any) -> tuple[Mapping[str, Any], Any, Any]:
    """
    Return (settings_mapping, org_id, org_country) for an org-like input.

    Accepts an ORM Organization, a dict shaped like {"settings": {...}}, a bare
    settings mapping, or None. Never raises.
    """
    if org is None:
        return {}, None, None

    if isinstance(org, Mapping):
        nested = org.get("settings")
        if isinstance(nested, Mapping):
            return nested, org.get("id"), org.get("country")
        # Bare settings mapping (e.g. the AI financial context dict).
        return org, org.get("id"), org.get("country")

    org_settings = getattr(org, "settings", None)
    if not isinstance(org_settings, Mapping):
        org_settings = {}
    return org_settings, getattr(org, "id", None), getattr(org, "country", None)


def resolve_primary_currency(org: Any = None) -> str:
    """
    Single canonical resolver for an organization's primary currency.

    Precedence (first valid wins):
      1. settings['primary_currency']            -- current canonical key
      2. settings['currency']                    -- legacy key kept in sync
      3. settings['template_applied_currency']   -- set by the onboarding template
      4. country default, derived from settings['country'] /
         settings['template_applied_region'] / org.country
      5. DEFAULT_CURRENCY ("USD") -- logged as a warning, since falling back here
         means the org is being priced in a currency nobody chose.

    Tolerates org=None, org.settings=None and org.settings={} without raising.

    Args:
        org: Organization ORM object, {"settings": {...}} dict, bare settings
             mapping, or None.

    Returns:
        A valid currency code.
    """
    org_settings, org_id, org_country = _extract_org_settings(org)

    for key in ("primary_currency", "currency", "template_applied_currency"):
        code = _coerce_currency_code(org_settings.get(key))
        if code:
            return code

    country_candidates = (
        org_settings.get("country"),
        org_settings.get("template_applied_region"),
        org_country,
    )
    for candidate in country_candidates:
        raw = getattr(candidate, "value", candidate)
        if not isinstance(raw, str) or not raw.strip():
            continue
        derived = COUNTRY_DEFAULT_CURRENCY.get(raw.strip().upper())
        if derived:
            logger.info(
                "Primary currency derived from country (organization has no explicit currency)",
                org_id=org_id,
                country=raw.strip().upper(),
                resolved_currency=derived,
                module="currency",
                function="resolve_primary_currency",
            )
            return derived

    logger.warning(
        "Primary currency could not be resolved; falling back to default. "
        "Amounts may be priced in the wrong currency until it is persisted.",
        org_id=org_id,
        fallback_currency=DEFAULT_CURRENCY,
        module="currency",
        function="resolve_primary_currency",
    )
    return DEFAULT_CURRENCY


def format_currency(
    amount: float | Decimal | Money, currency: str = "USD", use_grouping: bool = True
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
    precision = Decimal("1") if decimal_places == 0 else Decimal("0.1") ** decimal_places
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
            grouped_parts.append(reversed_str[i : i + grouping])
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
    amount: float | Decimal | Money, from_currency: str, to_currency: str
) -> float | Decimal | Money:
    """
    Convert amount from one currency to another
    ESTÁNDAR NOUGRAM: Usa Money para precisión en conversiones

    Same-currency is the happy path: the amount is returned untouched, with no
    rate lookup, no warning and no precision loss (a Decimal stays a Decimal).

    Args:
        amount: Amount to convert (Money, Decimal, or float)
        from_currency: Source currency code. Si amount es Money, se usa su currency
        to_currency: Target currency code

    Returns:
        Converted amount (Money si input es Money, Decimal si input es Decimal,
        float para compatibilidad)
    """
    # ESTÁNDAR NOUGRAM: Si es Money, usar su currency
    is_money = isinstance(amount, Money)
    is_decimal = isinstance(amount, Decimal)
    if is_money:
        from_currency = amount.currency
        amount_decimal = amount.amount
    elif is_decimal:
        amount_decimal = amount
    else:
        amount_decimal = Decimal(str(amount))

    normalized_from = (from_currency or "").upper()
    normalized_to = (to_currency or "").upper()

    if normalized_from == normalized_to:
        # No conversion at all: return the very same value that came in.
        if is_money:
            return amount
        if is_decimal:
            return amount_decimal
        return float(amount_decimal)

    _warn_placeholder_conversion(normalized_from, normalized_to)

    # ESTÁNDAR NOUGRAM: Convertir usando Decimal para precisión
    # Convert to USD first (base currency)
    amount_in_usd = amount_decimal / get_exchange_rate_to_usd(normalized_from)

    # Convert from USD to target currency
    converted_decimal = amount_in_usd * get_exchange_rate_to_usd(normalized_to)

    # Retornar Money si input era Money, Decimal si era Decimal, float legacy
    if is_money:
        return Money(converted_decimal, to_currency)
    if is_decimal:
        return converted_decimal
    return float(converted_decimal)


def normalize_to_primary_currency(
    amount: float | Decimal | Money,
    from_currency: str | None,
    primary_currency: str = DEFAULT_CURRENCY,
) -> float | Decimal | Money:
    """
    Normalize amount to primary currency
    ESTÁNDAR NOUGRAM: Usa Money para precisión en normalización

    This is used for calculations where all costs need to be in the same currency.

    Args:
        amount: Amount to normalize (Money, Decimal, or float)
        from_currency: Source currency code (can be None, defaults to USD). Si amount es Money, se ignora
        primary_currency: Target primary currency code (default: USD)

    Returns:
        Normalized amount in primary currency (Money si input es Money, Decimal si
        input es Decimal, float para compatibilidad)
    """
    # ESTÁNDAR NOUGRAM: Si es Money, usar su currency
    is_money = isinstance(amount, Money)
    if is_money:
        from_currency = amount.currency

    # Handle None or empty currency.
    # Un código presente pero NO soportado (p.ej. "CLP" persistido por una ruta que
    # no valida) se sustituye por el default, lo que equivale a no convertir: un
    # sueldo de 500.000 CLP entra a una org COP como 2.000.000.000. La sustitución
    # se mantiene (no romper lecturas históricas) pero deja de ser silenciosa.
    for raw_code in (from_currency, primary_currency):
        coerced = _coerce_currency_code(raw_code)
        if coerced is None and isinstance(getattr(raw_code, "value", raw_code), str):
            if str(getattr(raw_code, "value", raw_code)).strip():
                _warn_unknown_currency(str(raw_code), "normalize_to_primary_currency")

    from_currency = _coerce_currency_code(from_currency) or DEFAULT_CURRENCY
    primary_currency = _coerce_currency_code(primary_currency) or DEFAULT_CURRENCY

    return convert_currency(amount, from_currency, primary_currency)
