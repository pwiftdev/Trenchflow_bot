from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.handlers.help import help_command


@pytest.mark.asyncio
async def test_help_replies_with_scan_section() -> None:
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()

    await help_command(update, MagicMock())

    update.message.reply_text.assert_awaited_once()
    text = update.message.reply_text.await_args.args[0]
    assert "/scan" in text
    assert "Argus" in text
