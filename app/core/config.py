from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Consumer Intelligence"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "local"
    DEBUG: bool = False

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    # TEST-002: production-safe default (bcrypt's own recommended cost
    # factor). Only tests/conftest.py overrides this, to a much cheaper
    # value, via the BCRYPT_ROUNDS env var set before any app import --
    # see app/core/security.py for the full rationale.
    BCRYPT_ROUNDS: int = 12
    INTERNAL_SERVICE_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    AUTH_LOCKOUT_MINUTES: int = 15
    AUTH_MAX_FAILED_ATTEMPTS: int = 5
    AUTH_SESSION_EXPIRE_DAYS: int = 90
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_AUDIENCE: str = "ai-consumer-intelligence-api"
    JWT_ISSUER: str = "ai-consumer-intelligence"

    AICI_CACHE_BACKEND: str = "memory"
    AICI_REDIS_URL: str = "redis://redis:6379/0"

    CORS_ALLOWED_ORIGINS: str = ""
    TRUSTED_HOSTS: str = ""
    MAX_REQUEST_BODY_BYTES: int = 2_097_152
    EXPOSE_API_DOCS: bool = True

    # CLIENT-002f: password-reset email links + token lifetime. EMAIL_PROVIDER
    # only supports "log" for now (real SMTP/third-party provider is a
    # pending decision, see ADR-013) -- do not add other values here without
    # that decision first.
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    EMAIL_PROVIDER: str = "log"
    PASSWORD_RESET_TOKEN_MINUTES: int = 30

    # BILL-001: payment provider abstraction, same env-driven-factory
    # pattern as EMAIL_PROVIDER above -- defaults to a mock provider that
    # never touches real money; switching to "stripe" requires
    # STRIPE_SECRET_KEY to be set (see ADR-016, app/domains/billing/factory.py).
    PAYMENT_PROVIDER: str = "mock"
    STRIPE_SECRET_KEY: str | None = None
    # FREE tier watchlist item cap -- single source of truth, referenced
    # from watchlist_router.py's quota check instead of a magic number.
    FREE_TIER_WATCHLIST_LIMIT: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
