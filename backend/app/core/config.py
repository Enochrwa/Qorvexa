"""Application settings, loaded from the environment (see .env.example)."""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "Qorvexa"
    cors_origins: str = "http://localhost:5173"
    database_url: str = "postgresql+asyncpg://qorvexa:change-me@localhost:5432/qorvexa"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = Field(default="dev-only-change-me", min_length=8)
    log_level: str = "INFO"
    frontend_url: str = "http://localhost:5173"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 30
    cookie_secure: bool = False
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    email_from: str = "no-reply@qorvexa.local"
    # Number of trusted reverse proxies in front of the app (Render = 1). 0 ignores X-Forwarded-For.
    trusted_proxy_count: int = 0
    max_profiles_per_account: int = 5
    # Maturity limit for anonymous requests and requests without an X-Profile-Id (ADR-0013).
    public_maturity_limit: str = "13+"
    verify_email_ttl_hours: int = 24
    password_reset_ttl_hours: int = 1

    @model_validator(mode="after")
    def _require_real_secrets_in_production(self) -> "Settings":
        if self.app_env == "production" and (
            self.jwt_secret == "dev-only-change-me"  # noqa: S105
            or len(self.jwt_secret) < 32
        ):
            raise ValueError("JWT_SECRET must be set to a random value of 32+ characters")
        if self.app_env == "production" and not self.cookie_secure:
            raise ValueError("COOKIE_SECURE must be true in production")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
