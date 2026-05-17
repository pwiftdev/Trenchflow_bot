from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import BotCommand
from telegram.error import ChatMigrated

from bot.commands import FOUNDERS_COMMANDS, PUBLIC_COMMANDS, register_bot_commands
from config.settings import Settings


@pytest.mark.asyncio
async def test_register_bot_commands_sets_public_scopes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("FOUNDERS_CHAT_ID", "")
    get_settings = __import__("config.settings", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()
    settings = get_settings()

    bot = MagicMock()
    bot.set_my_commands = AsyncMock()

    await register_bot_commands(bot, settings)

    assert bot.set_my_commands.await_count == 3
    for call in bot.set_my_commands.await_args_list[:3]:
        commands = call.args[0]
        assert commands[0] == BotCommand("scan", PUBLIC_COMMANDS[0].description)
        assert commands[1] == BotCommand("help", PUBLIC_COMMANDS[1].description)


@pytest.mark.asyncio
async def test_register_bot_commands_adds_founders_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("FOUNDERS_CHAT_ID", "-5210686805")
    get_settings = __import__("config.settings", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()

    settings = Settings(telegram_bot_token="test-token", founders_chat_id=-5210686805)
    bot = MagicMock()
    bot.set_my_commands = AsyncMock()

    await register_bot_commands(bot, settings)

    assert bot.set_my_commands.await_count == 4
    founders_call = bot.set_my_commands.await_args_list[-1]
    commands = founders_call.args[0]
    assert len(commands) == len(PUBLIC_COMMANDS) + len(FOUNDERS_COMMANDS)
    assert commands[-1].command == "founderstest"


@pytest.mark.asyncio
async def test_register_bot_commands_retries_on_chat_migrated() -> None:
    settings = Settings(telegram_bot_token="test-token", founders_chat_id=-5210686805)
    bot = MagicMock()
    new_chat_id = -1003938424856
    bot.set_my_commands = AsyncMock(
        side_effect=[
            None,
            None,
            None,
            ChatMigrated(new_chat_id),
            None,
        ]
    )

    await register_bot_commands(bot, settings)

    assert bot.set_my_commands.await_count == 5
    retry_call = bot.set_my_commands.await_args_list[-1]
    assert retry_call.kwargs["scope"].chat_id == new_chat_id
