from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = Field(validation_alias="TELEGRAM_BOT_TOKEN")
    founders_chat_id: Optional[int] = Field(
        default=None,
        validation_alias="FOUNDERS_CHAT_ID",
        description="Alpha / founders feed — every group scan is posted here.",
    )

    helius_api_key: Optional[str] = Field(default=None, validation_alias="HELIUS_API_KEY")
    helius_timeout_seconds: float = Field(
        default=10.0,
        validation_alias="HELIUS_TIMEOUT_SECONDS",
    )
    helius_webhook_secret: Optional[str] = Field(
        default=None, validation_alias="HELIUS_WEBHOOK_SECRET"
    )
    birdeye_api_key: Optional[str] = Field(default=None, validation_alias="BIRDEYE_API_KEY")
    birdeye_base_url: str = Field(
        default="https://public-api.birdeye.so",
        validation_alias="BIRDEYE_BASE_URL",
    )
    birdeye_timeout_seconds: float = Field(
        default=10.0,
        validation_alias="BIRDEYE_TIMEOUT_SECONDS",
    )
    birdeye_chain: str = Field(default="solana", validation_alias="BIRDEYE_CHAIN")
    birdeye_holder_profile_interval: str = Field(
        default="1h",
        validation_alias="BIRDEYE_HOLDER_PROFILE_INTERVAL",
    )

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

    @field_validator("birdeye_api_key", mode="before")
    @classmethod
    def normalize_birdeye_api_key(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        cleaned = value.strip().strip('"').strip("'")
        return cleaned or None

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
