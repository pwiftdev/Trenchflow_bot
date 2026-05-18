import pytest

from bot import runtime as app_runtime
from config.settings import Settings


@pytest.fixture
async def app_runtime_started(monkeypatch: pytest.MonkeyPatch) -> None:
    """Initialize shared HTTP clients and DB pool for tests that need them."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    settings = Settings(telegram_bot_token="test-token", birdeye_api_key="test-birdeye")
    await app_runtime.startup(settings)
    yield
    await app_runtime.shutdown()
