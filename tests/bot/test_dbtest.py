from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.dbtest import dbtest_command


@pytest.mark.asyncio
async def test_dbtest_missing_database_url() -> None:
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()

    with patch(
        "bot.handlers.dbtest.get_settings",
        return_value=MagicMock(database_url=None),
    ):
        await dbtest_command(update, MagicMock())

    update.message.reply_text.assert_awaited_once_with("DATABASE_URL is not set in .env")


@pytest.mark.asyncio
async def test_dbtest_connected() -> None:
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_factory = MagicMock(return_value=mock_session)
    mock_engine = AsyncMock()
    mock_engine.dispose = AsyncMock()

    mock_settings = MagicMock(database_url="postgresql://u:p@h/db")

    with patch("bot.handlers.dbtest.get_settings", return_value=mock_settings), patch(
        "bot.handlers.dbtest.create_engine", return_value=mock_engine
    ), patch("bot.handlers.dbtest.create_session_factory", return_value=mock_factory), patch(
        "bot.handlers.dbtest.ping_database", AsyncMock(return_value=True)
    ):
        await dbtest_command(update, MagicMock())

    update.message.reply_text.assert_awaited_once_with("DB connected")
