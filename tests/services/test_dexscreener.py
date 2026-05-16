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
        "priceChange": {"h24": 5},
        "info": {"imageUrl": "https://example.com/a.png"},
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
        "priceChange": {"h24": 10},
        "info": {"imageUrl": "https://example.com/b.png"},
    },
]

MINT = "TokenMint1111111111111111111111111111111111"


def test_select_best_pair_prefers_highest_liquidity() -> None:
    best = _select_best_pair(SAMPLE_PAIRS, MINT)
    assert best is not None
    assert best["dexId"] == "pumpfun"


def test_pair_to_snapshot_maps_fields() -> None:
    pair = _select_best_pair(SAMPLE_PAIRS, MINT)
    assert pair is not None
    snapshot = _pair_to_snapshot(pair, MINT)
    assert snapshot.symbol == "MEME"
    assert snapshot.market_cap == 500000
    assert snapshot.image_url == "https://example.com/b.png"
