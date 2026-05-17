import os

import pytest

from config.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_empty_founders_chat_id_treated_as_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("FOUNDERS_CHAT_ID", "")
    monkeypatch.setenv("ENV", "dev")

    settings = Settings()

    assert settings.founders_chat_id is None


def test_founders_chat_id_parses_integer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("FOUNDERS_CHAT_ID", "-1001234567890")
    monkeypatch.setenv("ENV", "dev")

    settings = Settings()

    assert settings.founders_chat_id == -1001234567890


def test_birdeye_api_key_strips_quotes_and_whitespace(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("BIRDEYE_API_KEY", '  "abc123"  ')
    monkeypatch.setenv("ENV", "dev")

    settings = Settings()

    assert settings.birdeye_api_key == "abc123"
