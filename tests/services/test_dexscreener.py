from services.dexscreener import _pair_to_snapshot, _select_best_pair


SAMPLE_PAIRS = [
    {
        "chainId": "solana",
        "dexId": "raydium",
        "url": "https://dexscreener.com/solana/low",
        "baseToken": {
            "address": "TokenMint1111111111111111111111111111111111",
            "name": "Meme",
            "symbol": "MEME",
        },
        "quoteToken": {"address": "So11111111111111111111111111111111111111112", "symbol": "SOL"},
        "priceUsd": "0.001",
        "marketCap": 100000,
        "liquidity": {"usd": 5000},
        "volume": {"h24": 1000},
        "priceChange": {"h1": 5, "h24": 12},
        "txns": {"h1": {"buys": 10, "sells": 8}},
        "pairCreatedAt": 1_700_000_000_000,
        "boosts": {"active": 0},
        "info": {"imageUrl": "https://example.com/a.png", "header": "https://example.com/h.png"},
    },
    {
        "chainId": "solana",
        "dexId": "pumpfun",
        "url": "https://dexscreener.com/solana/high",
        "baseToken": {
            "address": "TokenMint1111111111111111111111111111111111",
            "name": "Meme",
            "symbol": "MEME",
        },
        "quoteToken": {"address": "So11111111111111111111111111111111111111112", "symbol": "SOL"},
        "priceUsd": "0.002",
        "marketCap": 500000,
        "liquidity": {"usd": 50000},
        "volume": {"h24": 20000},
        "priceChange": {"h1": 10, "h24": 20},
        "txns": {"h1": {"buys": 100, "sells": 90}},
        "pairCreatedAt": 1_700_000_000_000,
        "boosts": {"active": 2},
        "info": {"imageUrl": "https://example.com/b.png"},
    },
]

MINT = "TokenMint1111111111111111111111111111111111"


def test_select_best_pair_prefers_highest_liquidity() -> None:
    best = _select_best_pair(SAMPLE_PAIRS, MINT)
    assert best is not None
    assert best["dexId"] == "pumpfun"


def test_pair_to_snapshot_maps_extended_fields() -> None:
    pair = _select_best_pair(SAMPLE_PAIRS, MINT)
    assert pair is not None
    snapshot = _pair_to_snapshot(pair, MINT)
    assert snapshot.symbol == "MEME"
    assert snapshot.txns_h1_buys == 100
    assert snapshot.boosts_active == 2
    assert snapshot.header_image_url is None or snapshot.image_url
