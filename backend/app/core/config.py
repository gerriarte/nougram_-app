"""
Application configuration and settings
"""

import logging
from decimal import Decimal, InvalidOperation

from pydantic_settings import BaseSettings

# stdlib logger a propósito: app.core.logging importa este módulo, así que usar el
# logger estructurado acá crearía un import circular.
logger = logging.getLogger(__name__)

# Baseline exchange rates expressed as "units of <currency> per 1 USD".
# Kept as strings on purpose: they are turned into Decimal downstream and money
# must never round-trip through float (ESTÁNDAR NOUGRAM).
# These are the historical hardcoded values, now explicit and overridable via the
# EXCHANGE_RATES_TO_USD env var. They are placeholders, not market data.
DEFAULT_EXCHANGE_RATES_TO_USD: dict[str, str] = {
    "USD": "1",  # Base currency
    "COP": "4000",
    "ARS": "850",
    "EUR": "0.92",
    "PEN": "3.7",
    "MXN": "17",
}


def parse_exchange_rate(code: object, value: object) -> Decimal | None:
    """
    Validate one "units per 1 USD" override entry.

    Returns the parsed Decimal, or None (logging an error) when the value is not a
    finite positive number. Rejecting here is what keeps a typo in
    EXCHANGE_RATES_TO_USD from either crashing the import of app.core.currency
    (Decimal("4.150,00") -> InvalidOperation) or silently producing a division by
    zero / a sign-flipped conversion downstream.
    """
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, ArithmeticError):
        logger.error(
            "Invalid EXCHANGE_RATES_TO_USD entry ignored (not a number): %s=%r", code, value
        )
        return None
    if not parsed.is_finite() or parsed <= 0:
        logger.error(
            "Invalid EXCHANGE_RATES_TO_USD entry ignored (must be > 0): %s=%r", code, value
        )
        return None
    return parsed


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """

    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    SESSION_INACTIVITY_TIMEOUT_MINUTES: int = 10
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 60
    EMAIL_VERIFICATION_REQUIRED: bool = False
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 1440

    # Google OAuth (opcional - vacío si no se usa)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_SERVICE_ACCOUNT_PATH: str = ""

    # Google Sheets (opcional - vacío si no se usa)
    GOOGLE_SHEETS_ID: str = ""

    # AI Configuration
    AI_PROVIDER: str = "openai"  # Supported: "openai"
    AI_MODEL: str = "gpt-4o-mini"
    AI_TIMEOUT_SECONDS: int = 30
    AI_MAX_RETRIES: int = 2
    OPENAI_API_KEY: str = ""
    GOOGLE_AI_API_KEY: str = ""

    # Email — Resend
    RESEND_API_KEY: str = ""
    RESEND_BASE_URL: str = "https://api.resend.com"
    RESEND_FROM_EMAIL: str = ""
    RESEND_FROM_NAME: str = "Nougram"
    # Optional: Resend dashboard template id (or published alias) for password reset
    RESEND_TEMPLATE_PASSWORD_RESET_ID: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:5000"

    # Environment
    ENVIRONMENT: str = "development"
    CREATE_SCHEMA_ON_STARTUP: bool = False
    SUPER_ADMIN_EMAIL: str = "gerardoriarte@gmail.com"
    SUPER_ADMIN_ALLOWED_EMAILS: str = ""
    AUTO_PROVISION_SUPER_ADMIN: bool = False
    SUPER_ADMIN_BOOTSTRAP_PASSWORD: str = ""
    SUPER_ADMIN_BOOTSTRAP_FULL_NAME: str = "Super Admin"
    SUPER_ADMIN_BOOTSTRAP_FORCE_PASSWORD_RESET: bool = False

    # Feature flags (roles)
    FEATURE_ROLES: bool = False
    FEATURE_ROLES_ENFORCE: bool = False
    FEATURE_TEAM_CELLS: bool = False

    # Stripe Configuration
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_IDS: str = "{}"  # JSON string with price IDs per plan

    # Billing provider abstraction
    # Supported values: "manual", "stripe"
    PAYMENT_GATEWAY_PROVIDER: str = "manual"

    # Exchange Rate API Configuration
    EXCHANGE_RATE_API_KEY: str = ""  # API key for exchangerate-api.com (free tier available)
    EXCHANGE_RATE_API_URL: str = "https://api.exchangerate-api.com/v4/latest"  # Free tier endpoint

    # Exchange rates used for cross-currency normalization.
    # No external API is called: the rates below are static and auditable.
    # EXCHANGE_RATES_TO_USD is a JSON object that OVERRIDES (merges over)
    # DEFAULT_EXCHANGE_RATES_TO_USD, e.g. '{"COP": "4150", "ARS": "1050"}'.
    EXCHANGE_RATES_TO_USD: str = ""
    # Date the configured rates were taken (ISO-8601). Exposed by the API so any
    # converted figure can be audited against the rate vintage that produced it.
    EXCHANGE_RATES_AS_OF: str = "2024-01-01"
    # Origin of the rates. Any value starting with "placeholder" marks them as
    # non-authoritative and makes cross-currency conversions log a warning.
    EXCHANGE_RATES_SOURCE: str = "placeholder:hardcoded-defaults"

    # Frontend URL for invitation links
    FRONTEND_URL: str = "http://localhost:3000"  # Frontend URL for invitation links

    # Contabo Object Storage (S3-compatible) for proposal assets
    CONTABO_S3_ENDPOINT_URL: str = ""
    CONTABO_S3_REGION: str = ""
    CONTABO_S3_BUCKET: str = ""
    CONTABO_S3_ACCESS_KEY_ID: str = ""
    CONTABO_S3_SECRET_ACCESS_KEY: str = ""
    CONTABO_S3_PUBLIC_BASE_URL: str = ""

    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"  # Redis broker URL
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"  # Redis result backend

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string; skip empty entries."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o and o.strip()]

    @property
    def exchange_rates_to_usd_dict(self) -> dict[str, str]:
        """
        Effective exchange rates (units per 1 USD) as strings, ready for Decimal.

        DEFAULT_EXCHANGE_RATES_TO_USD merged with the EXCHANGE_RATES_TO_USD JSON
        override. A malformed override is ignored so a bad env var can never take
        the app down; the defaults keep applying. That guarantee is enforced
        entry by entry: every value must parse as a finite Decimal > 0, otherwise
        it is dropped with a logger.error and the default rate survives.
        """
        import json

        rates = dict(DEFAULT_EXCHANGE_RATES_TO_USD)
        raw = (self.EXCHANGE_RATES_TO_USD or "").strip()
        if not raw:
            return rates
        try:
            override = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.error("EXCHANGE_RATES_TO_USD is not valid JSON; using default rates")
            return rates
        if not isinstance(override, dict):
            logger.error("EXCHANGE_RATES_TO_USD must be a JSON object; using default rates")
            return rates
        for code, value in override.items():
            if value is None:
                continue
            normalized_code = str(code).strip().upper()
            if not normalized_code:
                logger.error("Invalid EXCHANGE_RATES_TO_USD entry ignored (empty currency code)")
                continue
            parsed = parse_exchange_rate(normalized_code, value)
            if parsed is None:
                continue
            rates[normalized_code] = str(parsed)
        return rates

    @property
    def exchange_rates_are_placeholder(self) -> bool:
        """True while the configured rates are the non-authoritative defaults."""
        return (self.EXCHANGE_RATES_SOURCE or "").strip().lower().startswith("placeholder")

    @property
    def stripe_price_ids_dict(self) -> dict:
        """Parse Stripe price IDs from JSON string"""
        import json

        try:
            return json.loads(self.STRIPE_PRICE_IDS)
        except (json.JSONDecodeError, TypeError):
            return {}

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in environment (e.g., deprecated APOLLO_API_KEY)


# Create settings instance
settings = Settings()
