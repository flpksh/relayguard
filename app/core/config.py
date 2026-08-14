from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_TOKEN_SECRET = "development-only-token-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "RelayGuard"
    app_env: Literal["development", "test", "production"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "postgresql+asyncpg://relayguard:relayguard@db:5432/relayguard"
    access_token_secret: SecretStr = SecretStr(DEVELOPMENT_TOKEN_SECRET)
    access_token_previous_secret: SecretStr | None = None
    access_token_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)
    access_token_issuer: str = "relayguard"
    access_token_audience: str = "relayguard-api"
    auth_rate_limit_requests: int = Field(default=10, ge=1, le=1000)
    auth_rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)

    @model_validator(mode="after")
    def validate_token_secret(self) -> "Settings":
        secret = self.access_token_secret.get_secret_value()
        if len(secret) < 32:
            raise ValueError("ACCESS_TOKEN_SECRET deve conter pelo menos 32 caracteres")
        if self.app_env == "production" and secret == DEVELOPMENT_TOKEN_SECRET:
            raise ValueError("ACCESS_TOKEN_SECRET deve ser alterado em produção")
        if self.access_token_previous_secret is not None:
            previous = self.access_token_previous_secret.get_secret_value()
            if len(previous) < 32:
                raise ValueError(
                    "ACCESS_TOKEN_PREVIOUS_SECRET deve conter pelo menos 32 caracteres"
                )
            if previous == secret:
                raise ValueError("os segredos atual e anterior devem ser diferentes")
        return self

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace(
            "postgresql+asyncpg://", "postgresql+psycopg2://", 1
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
