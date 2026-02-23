"""
Application configuration and settings
"""
from pydantic_settings import BaseSettings
from typing import List


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
    
    # Google OAuth (opcional - vacío si no se usa)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_SERVICE_ACCOUNT_PATH: str = ""
    
    # Google Sheets (opcional - vacío si no se usa)
    GOOGLE_SHEETS_ID: str = ""
    
    # AI Configuration
    OPENAI_API_KEY: str = ""
    GOOGLE_AI_API_KEY: str = ""
    
    # Email Configuration (SMTP)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Nougram"
    SMTP_USE_TLS: bool = True
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:5000"
    
    # Environment
    ENVIRONMENT: str = "development"
    SUPER_ADMIN_EMAIL: str = "gerardoriarte@gmail.com"
    SUPER_ADMIN_ALLOWED_EMAILS: str = ""
    AUTO_PROVISION_SUPER_ADMIN: bool = False
    SUPER_ADMIN_BOOTSTRAP_PASSWORD: str = ""
    SUPER_ADMIN_BOOTSTRAP_FULL_NAME: str = "Super Admin"
    SUPER_ADMIN_BOOTSTRAP_FORCE_PASSWORD_RESET: bool = False

    # Feature flags (roles)
    FEATURE_ROLES: bool = False
    FEATURE_ROLES_ENFORCE: bool = False
    
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
    
    # Frontend URL for invitation links
    FRONTEND_URL: str = "http://localhost:3000"  # Frontend URL for invitation links
    
    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"  # Redis broker URL
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"  # Redis result backend
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
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
