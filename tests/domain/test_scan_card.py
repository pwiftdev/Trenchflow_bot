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


def test_format_ath_shows_price_and_drawdown() -> None:
    snapshot = TokenSnapshot(
        mint="Mint1111111111111111111111111111111111111",
        symbol="T",
        name="T",
        price_usd=0.0005,
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
        ath_price_usd=0.001,
    )
    meta = ScanMeta(
        scanner_display="x",
        scanned_at=datetime(2026, 5, 16, tzinfo=timezone.utc),
        chat_title=None,
    )
    text = format_scan_card(snapshot, meta, None)
    assert "ATH:" in text
    assert "from ATH" in text


def test_format_dex_paid_green_when_paid_red_when_not() -> None:
    meta = ScanMeta(
        scanner_display="x",
        scanned_at=datetime(2026, 5, 16, tzinfo=timezone.utc),
        chat_title=None,
    )
    base = dict(
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
    paid = format_scan_card(
        TokenSnapshot(**base, dex_profile_paid=True),
        meta,
        None,
    )
    unpaid = format_scan_card(
        TokenSnapshot(**base, dex_profile_paid=False),
        meta,
        None,
    )
    assert "└ DEX Paid: 🟢 Paid" in paid
    assert "└ DEX Paid: 🔴" in unpaid
