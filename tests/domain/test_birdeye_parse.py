from domain.birdeye_parse import (
    holder_count_from_overview,
    merge_security,
    overview_to_snapshot,
    security_from_birdeye,
)
from domain.security_snapshot import SecuritySnapshot


OVERVIEW_SAMPLE = {
    "address": "Mint1111111111111111111111111111111111111",
    "symbol": "MEME",
    "name": "Meme Coin",
    "price": 0.00042,
    "marketCap": 420_000,
    "fdv": 500_000,
    "liquidity": 25_000,
    "v24hUSD": 150_000,
    "priceChange1hPercent": 5.5,
    "priceChange24hPercent": -12.3,
    "buy1h": 120,
    "sell1h": 98,
    "holder": 3_400,
    "logoURI": "https://example.com/logo.png",
    "extensions": {
        "website": "https://example.com",
        "twitter": "https://x.com/meme",
        "telegram": None,
    },
}

SECURITY_SAMPLE = {
    "top10HolderPercent": 0.304,
    "totalSupply": 1_000_000_000,
    "freezeAuthority": None,
    "freezeable": None,
    "creatorPercentage": 0.0000001,
    "creationTime": 1_700_000_000,
}


def test_overview_to_snapshot_maps_market_fields() -> None:
    mint = "Mint1111111111111111111111111111111111111"
    snapshot = overview_to_snapshot(OVERVIEW_SAMPLE, mint)

    assert snapshot.symbol == "MEME"
    assert snapshot.price_usd == 0.00042
    assert snapshot.market_cap == 420_000
    assert snapshot.volume_h24 == 150_000
    assert snapshot.txns_h1_buys == 120
    assert snapshot.txns_h1_sells == 98
    assert snapshot.image_url == "https://example.com/logo.png"
    assert "birdeye.so/token/" in (snapshot.pair_url or "")


def test_security_from_birdeye_scales_top10_and_dev_sold() -> None:
    security = security_from_birdeye(
        SECURITY_SAMPLE,
        holder_count=holder_count_from_overview(OVERVIEW_SAMPLE),
    )

    assert security.top10_holder_pct == 30.4
    assert security.holder_count == 3_400
    assert security.freeze_renounced is True
    assert security.dev_sold_label == "🟢"
    assert security.supply_ui == "1B"


def test_merge_security_prefers_birdeye_fills_mint_from_helius() -> None:
    birdeye = SecuritySnapshot(
        freeze_renounced=True,
        top10_holder_pct=20.0,
        holder_count=100,
    )
    helius = SecuritySnapshot(
        mint_renounced=True,
        holder_count=99,
        top10_holder_pct=15.0,
    )

    merged = merge_security(birdeye, helius)

    assert merged is not None
    assert merged.mint_renounced is True
    assert merged.holder_count == 100
    assert merged.top10_holder_pct == 20.0
