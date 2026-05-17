from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram.error import BadRequest

from bot.scan_reply import reply_scan_card
from domain.token_snapshot import TokenSnapshot


def _snapshot() -> TokenSnapshot:
    return TokenSnapshot(
        mint="Mint1111111111111111111111111111111111111",
        symbol="T",
        name="Test",
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
        header_image_url="https://cdn.example.com/bad-banner.png",
        image_url="https://cdn.example.com/good-icon.png",
    )


@pytest.mark.asyncio
async def test_reply_scan_card_falls_back_after_bad_header() -> None:
    message = MagicMock()
    message.reply_photo = AsyncMock(
        side_effect=[BadRequest("failed to get HTTP URL content"), None]
    )
    message.reply_text = AsyncMock()
    keyboard = MagicMock()

    await reply_scan_card(
        message,
        caption="cap",
        keyboard=keyboard,
        snapshot=_snapshot(),
    )

    assert message.reply_photo.await_count == 2
    assert message.reply_photo.await_args_list[1].kwargs["photo"] == (
        "https://cdn.example.com/good-icon.png"
    )
    assert message.reply_photo.await_args_list[1].kwargs["reply_markup"] is keyboard
    message.reply_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_reply_scan_card_text_only_when_all_photos_fail() -> None:
    message = MagicMock()
    message.reply_photo = AsyncMock(side_effect=BadRequest("bad"))
    message.reply_text = AsyncMock()
    keyboard = MagicMock()

    await reply_scan_card(
        message,
        caption="cap",
        keyboard=keyboard,
        snapshot=_snapshot(),
    )

    message.reply_text.assert_awaited_once()
    assert message.reply_text.await_args.kwargs["reply_markup"] is keyboard
