from domain.scan_card import ScanMeta, format_scan_card
from domain.trench_alert import TrenchAlert, HolderTagRow, holder_profile_from_birdeye
from domain.token_snapshot import TokenSnapshot
from datetime import datetime, timezone


HOLDER_PROFILE_SAMPLE = {
    "holder_summary": {
        "total_holder": 409,
        "percent_of_supply": 51.66,
    },
    "tags": [
        {
            "tag": "bundler",
            "holder_count": 404,
            "percent_of_supply": 50.45,
        },
        {
            "tag": "sniper",
            "holder_count": 0,
            "percent_of_supply": 0,
        },
        {
            "tag": "dev",
            "holder_count": 1,
            "percent_of_supply": 0,
        },
    ],
}


def test_holder_profile_from_birdeye_maps_tags() -> None:
    alert = holder_profile_from_birdeye(HOLDER_PROFILE_SAMPLE)

    assert alert.total_holders == 409
    assert alert.labeled_supply_pct == 51.66
    bundler = next(row for row in alert.tags if row.tag == "bundler")
    assert bundler.holder_count == 404
    assert bundler.percent_of_supply == 50.45
    sniper = next(row for row in alert.tags if row.tag == "sniper")
    assert sniper.holder_count == 0


def test_format_scan_card_includes_trench_alert() -> None:
    snapshot = TokenSnapshot(
        mint="Mint1111111111111111111111111111111111111",
        symbol="T",
        name="Test",
        price_usd=1.0,
        market_cap=1000.0,
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
    alert = TrenchAlert(
        total_holders=None,
        labeled_supply_pct=None,
        tags=(
            HolderTagRow("bundler", "Bundlers", 5, 20.0),
            HolderTagRow("sniper", "Snipers", 2, 5.0),
            HolderTagRow("insider", "Insiders", 0, 0.0),
            HolderTagRow("dev", "Dev", 1, 0.0),
            HolderTagRow("smart_trader", "Smart", 0, None),
        ),
    )
    meta = ScanMeta(
        scanner_display="x",
        scanned_at=datetime(2026, 5, 16, tzinfo=timezone.utc),
        chat_title=None,
    )

    text = format_scan_card(snapshot, meta, None, trench_alert=alert)

    assert "⚠️ Trench" in text
    assert "Bundlers 5" in text
    assert "Snipers 2" in text
    assert "Labeled:" not in text
