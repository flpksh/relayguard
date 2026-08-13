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
    access_token_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)

    @model_validator(mode="after")
    def validate_token_secret(self) -> "Settings":
        secret = self.access_token_secret.get_secret_value()
        if len(secret) < 32:
            raise ValueError("ACCESS_TOKEN_SECRET must contain at least 32 characters")
        if self.app_env == "production" and secret == DEVELOPMENT_TOKEN_SECRET:
            raise ValueError("ACCESS_TOKEN_SECRET must be changed in production")
        return self

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace(
            "postgresql+asyncpg://", "postgresql+psycopg2://", 1
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
