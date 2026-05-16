from datetime import datetime, timezone

from domain.alpha_feed import AlphaScanContext, format_alpha_scan_alert
from domain.token_snapshot import TokenSnapshot


def test_format_alpha_scan_alert_includes_group_and_mcap() -> None:
    snapshot = TokenSnapshot(
        mint="MintAddress1111111111111111111111111111111111",
        symbol="BAK",
        name="Bakardi",
        price_usd=0.001,
        market_cap=311_780,
        fdv=None,
        liquidity_usd=50_000,
        volume_h24=120_000,
        price_change_h1=None,
        price_change_h24=None,
        txns_h1_buys=None,
        txns_h1_sells=None,
        pair_created_at_ms=None,
        dex_id="pumpswap",
        labels=[],
    )
    ctx = AlphaScanContext(
        group_title="Alpha Hunters",
        group_id=-100123,
        scanner_display="Bakardi (@bakardisol)",
        scanned_at=datetime(2026, 5, 16, 11, 39, tzinfo=timezone.utc),
        first_call_line="🔥 First call Bakardi (@bakardisol) @ $311.78K",
        cross_group_count_30m=2,
    )
    text = format_alpha_scan_alert(snapshot, ctx)

    assert "Alpha Hunters" in text
    assert "Bakardi" in text
    assert "$311.78K" in text
    assert "First call" in text
    assert "2</b> groups scanned" in text
    assert "bakardisol" in text
