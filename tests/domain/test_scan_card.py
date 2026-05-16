from datetime import datetime, timezone

from domain.scan_card import ScanMeta, format_scan_card
from domain.security_snapshot import SecuritySnapshot
from domain.token_snapshot import TokenSnapshot


def test_format_scan_card_phanes_style_sections() -> None:
    snapshot = TokenSnapshot(
        mint="MintAddress1111111111111111111111111111111111",
        symbol="UNG",
        name="Avatard Ung",
        price_usd=0.0001473,
        market_cap=147_400,
        fdv=200_000,
        liquidity_usd=15_600,
        volume_h24=605_300,
        price_change_h1=21.0,
        price_change_h24=208.0,
        txns_h1_buys=3200,
        txns_h1_sells=2600,
        pair_created_at_ms=1_700_000_000_000,
        dex_id="pumpfun",
        labels=["pump"],
        pair_url="https://dexscreener.com/solana/abc",
        image_url="https://example.com/img.png",
        header_image_url="https://example.com/header.png",
        websites=[("Website", "https://example.com")],
        socials=[("twitter", "https://x.com/test")],
        boosts_active=1,
    )
    security = SecuritySnapshot(
        mint_renounced=True,
        freeze_renounced=True,
        top10_holder_pct=7.0,
        holder_count=1400,
        supply_ui="1B",
    )
    meta = ScanMeta(
        scanner_display="Alice (@alice)",
        scanned_at=datetime(2026, 5, 16, 13, 18, tzinfo=timezone.utc),
        chat_title="Alpha Group",
        first_call_line="🔥 First call Alice @ $147.4K",
    )

    text = format_scan_card(snapshot, meta, security)

    assert "📊" in text
    assert "├ USD:" in text
    assert "├ 1H:" in text
    assert "🔒" in text
    assert "Top 10:" in text
    assert "🔥 First call" in text
    assert "DEX Paid:" in text
