from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = Field(validation_alias="TELEGRAM_BOT_TOKEN")
    founders_chat_id: Optional[int] = Field(default=None, validation_alias="FOUNDERS_CHAT_ID")

    helius_api_key: Optional[str] = Field(default=None, validation_alias="HELIUS_API_KEY")
    helius_webhook_secret: Optional[str] = Field(
        default=None, validation_alias="HELIUS_WEBHOOK_SECRET"
    )
    birdeye_api_key: Optional[str] = Field(default=None, validation_alias="BIRDEYE_API_KEY")

    database_url: Optional[str] = Field(default=None, validation_alias="DATABASE_URL")
    redis_url: Optional[str] = Field(default=None, validation_alias="REDIS_URL")
    anthropic_api_key: Optional[str] = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    sentry_dsn: Optional[str] = Field(default=None, validation_alias="SENTRY_DSN")
    twitter_bearer: Optional[str] = Field(default=None, validation_alias="TWITTER_BEARER")

    env: Literal["dev", "prod"] = Field(default="dev", validation_alias="ENV")
    webhook_url: Optional[str] = Field(default=None, validation_alias="WEBHOOK_URL")

    dexscreener_base_url: str = Field(
        default="https://api.dexscreener.com",
        validation_alias="DEXSCREENER_BASE_URL",
    )
    dexscreener_timeout_seconds: float = Field(
        default=10.0,
        validation_alias="DEXSCREENER_TIMEOUT_SECONDS",
    )
    solana_chain_id: str = Field(default="solana", validation_alias="SOLANA_CHAIN_ID")

    @model_validator(mode="before")
    @classmethod
    def empty_env_values_are_none(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        return {
            key: None if isinstance(value, str) and not value.strip() else value
            for key, value in data.items()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
