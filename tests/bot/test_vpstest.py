from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.handlers.vpstest import vpstest_command


@pytest.mark.asyncio
async def test_vpstest_replies_vps_worked() -> None:
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()

    await vpstest_command(update, MagicMock())

    update.message.reply_text.assert_awaited_once_with("VPS worked")
