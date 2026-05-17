from datetime import datetime, timezone

from domain.scan_card import ScanMeta, format_scan_card
from domain.security_snapshot import SecuritySnapshot
from domain.token_snapshot import TokenSnapshot
from domain.telegram_caption import TELEGRAM_CAPTION_LIMIT
from domain.trench_alert import HolderTagRow, TrenchAlert


def test_format_scan_card_phanes_style_tree() -> None:
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
        dex_profile_paid=True,
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
        first_call_line="😈 alice @ $147.40K",
    )
    alert = TrenchAlert(
        total_holders=None,
        labeled_supply_pct=None,
        tags=(
            HolderTagRow("bundler", "Bundlers", 5, 20.0),
            HolderTagRow("sniper", "Snipers", 2, 5.0),
            HolderTagRow("insider", "Insiders", 0, 0.0),
            HolderTagRow("dev", "Dev", 1, 0.0),
            HolderTagRow("smart_trader", "Smart", 82, 2.0),
        ),
    )

    text = format_scan_card(snapshot, meta, security, trench_alert=alert)

    assert "💊" in text
    assert " ├" in text
    assert " └" in text
    assert "📊 Stats" in text
    assert "USD" not in text.split("📊 Stats")[1].split("🔗")[0]
    assert "├ MC" in text
    assert "🟩" in text and "🟥" in text
    assert "🔒 Security" in text
    security_block = text.split("🔒 Security", 1)[1].split("\n\n", 1)[0]
    assert "├ T10" in security_block
    assert "├ Holders" in security_block
    assert "├ DS" in security_block
    assert "└ DP" in security_block
    assert "🔗 Socials" in text
    assert ">Twitter</a>" in text
    assert ">DEF</a>" not in text
    assert "Bundlers" in text
    assert "Insiders" not in text
    trench = text.split("⚠️ Trench", 1)[1].split("\n\n", 1)[0]
    assert "supply" in trench
    assert "Dev" not in trench


def test_format_scan_card_fits_telegram_photo_caption() -> None:
    mint = "C2omVhcvt3DDY77S2KZzawFJQeETZofgZ4eNWwkXpump"
    snapshot = TokenSnapshot(
        mint=mint,
        symbol="BULLISH",
        name="Bullish Degen",
        price_usd=0.001487,
        market_cap=1_490_000,
        fdv=None,
        liquidity_usd=145_190,
        volume_h24=226_280,
        price_change_h1=-0.9,
        price_change_h24=3.3,
        txns_h1_buys=1100,
        txns_h1_sells=397,
        pair_created_at_ms=1_700_000_000_000,
        dex_id="pumpfun",
        labels=["pump"],
        websites=[("Website", "https://bullish.example")],
        socials=[("twitter", "https://x.com/bullish")],
        dex_profile_paid=True,
        ath_price_usd=0.054434,
    )
    security = SecuritySnapshot(
        mint_renounced=True,
        freeze_renounced=True,
        top10_holder_pct=23.0,
        holder_count=31_600,
        supply_ui="1000M",
        dev_sold_label="🔴2.9%",
    )
    meta = ScanMeta(
        scanner_display="Bakardi (@bakardisol)",
        scanned_at=datetime(2026, 5, 17, 9, 51, tzinfo=timezone.utc),
        chat_title="Test",
        first_call_line="😈 bakardisol @ $1.49M [+1%] (26m)",
    )
    alert = TrenchAlert(
        total_holders=None,
        labeled_supply_pct=None,
        tags=(
            HolderTagRow("bundler", "Bundlers", 444, 1.1),
            HolderTagRow("sniper", "Snipers", 3, 2.9),
            HolderTagRow("insider", "Insiders", 0, 0.0),
            HolderTagRow("dev", "Dev", 1, 2.9),
            HolderTagRow("smart_trader", "Smart", 82, 2.0),
        ),
    )

    text = format_scan_card(snapshot, meta, security, trench_alert=alert)

    assert len(text) <= TELEGRAM_CAPTION_LIMIT


def test_format_dex_paid_emoji() -> None:
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
    paid = format_scan_card(TokenSnapshot(**base, dex_profile_paid=True), meta, None)
    unpaid = format_scan_card(TokenSnapshot(**base, dex_profile_paid=False), meta, None)
    assert "DP 🟢" in paid
    assert "DP 🔴" in unpaid
