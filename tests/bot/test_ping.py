from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.handlers.ping import ping_command


@pytest.mark.asyncio
async def test_ping_replies_pong() -> None:
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()

    await ping_command(update, MagicMock())

    update.message.reply_text.assert_awaited_once_with("pong")


@pytest.mark.asyncio
async def test_ping_ignores_updates_without_message() -> None:
    update = MagicMock()
    update.message = None

    await ping_command(update, MagicMock())
