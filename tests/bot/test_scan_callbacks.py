from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.scan_callbacks import scan_callback
from bot.scan_keyboard import DELETE_CALLBACK, REFRESH_PREFIX
from bot.scan_pipeline import ScanResult
from domain.scan_card import ScanMeta
from domain.token_snapshot import TokenSnapshot
from datetime import datetime, timezone


def _snapshot() -> TokenSnapshot:
    return TokenSnapshot(
        mint="Mint1111111111111111111111111111111111111",
        symbol="T",
        name="T",
        price_usd=1.0,
        market_cap=1.0,
        fdv=None,
        liquidity_usd=None,
        volume_h24=None,
        price_change_h1=None,
        price_change_h24=None,
        txns_h1_buys=None,
        txns_h1_sells=None,
        pair_created_at_ms=None,
        dex_id=None,
    )


@pytest.mark.asyncio
async def test_scan_delete_removes_message() -> None:
    message = MagicMock()
    message.delete = AsyncMock()
    query = MagicMock()
    query.data = DELETE_CALLBACK
    query.answer = AsyncMock()
    query.message = message
    update = MagicMock()
    update.callback_query = query

    await scan_callback(update, MagicMock())

    query.answer.assert_awaited_once()
    message.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_scan_refresh_rebuilds_card() -> None:
    mint = "So11111111111111111111111111111111111111112"
    message = MagicMock()
    message.photo = [MagicMock()]
    query = MagicMock()
    query.data = f"{REFRESH_PREFIX}{mint}"
    query.answer = AsyncMock()
    query.message = message
    update = MagicMock()
    update.callback_query = query

    result = ScanResult(
        snapshot=_snapshot(),
        security=None,
        trench_alert=None,
        meta=ScanMeta(
            scanner_display="x",
            scanned_at=datetime(2026, 5, 17, tzinfo=timezone.utc),
            chat_title=None,
        ),
        caption="updated",
    )

    with (
        patch("bot.handlers.scan_callbacks.build_scan_result", AsyncMock(return_value=result)),
        patch("bot.handlers.scan_callbacks.edit_scan_card", AsyncMock()) as edit_mock,
    ):
        await scan_callback(update, MagicMock())

    edit_mock.assert_awaited_once()
