from domain.token_snapshot import TokenSnapshot
from bot.scan_keyboard import DELETE_CALLBACK, REFRESH_PREFIX, build_scan_keyboard

MINT = "So11111111111111111111111111111111111111112"


def _snapshot() -> TokenSnapshot:
    return TokenSnapshot(
        mint=MINT,
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
    )


def test_scan_keyboard_has_explorer_urls_and_actions() -> None:
    keyboard = build_scan_keyboard(_snapshot())
    assert len(keyboard.inline_keyboard) == 2

    explorers = keyboard.inline_keyboard[0]
    assert [btn.text for btn in explorers] == ["DEF", "DS", "GT", "EXP", "X"]
    assert all(btn.url for btn in explorers)

    actions = keyboard.inline_keyboard[1]
    assert len(actions) == 2
    assert actions[0].text == "REFRESH"
    assert actions[0].callback_data == f"{REFRESH_PREFIX}{MINT}"
    assert actions[1].text == "DELETE"
    assert actions[1].callback_data == DELETE_CALLBACK
