from datetime import datetime, timezone

from domain.scan_card import ScanMeta, format_scan_card
from domain.token_snapshot import TokenSnapshot


def test_format_scan_card_includes_scanner_and_mcap() -> None:
    snapshot = TokenSnapshot(
        mint="MintAddress1111111111111111111111111111111111",
        symbol="TEST",
        name="Test Token",
        price_usd=0.0012,
        market_cap=1_500_000,
        fdv=2_000_000,
        liquidity_usd=250_000,
        volume_h24=80_000,
        price_change_h24=12.5,
        dex_id="raydium",
        pair_url="https://dexscreener.com/solana/abc",
        image_url="https://example.com/img.png",
        websites=[("Website", "https://example.com")],
        socials=[("twitter", "https://x.com/test")],
    )
    meta = ScanMeta(
        scanner_display="Alice (@alice)",
        scanned_at=datetime(2026, 5, 15, 20, 0, tzinfo=timezone.utc),
        chat_title="Alpha Group",
    )

    text = format_scan_card(snapshot, meta)

    assert "$TEST" in text
    assert "MCap at scan" in text
    assert "$1.50M" in text
    assert "Alice (@alice)" in text
    assert "Alpha Group" in text
    assert "DexScreener" in text
