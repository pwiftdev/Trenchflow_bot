from domain.birdeye_parse import ath_high_from_ohlcv_items, ohlcv_candle_type_for_age_seconds


def test_ohlcv_candle_type_picks_finer_granularity_for_new_tokens() -> None:
    assert ohlcv_candle_type_for_age_seconds(3600) == "15m"
    assert ohlcv_candle_type_for_age_seconds(3 * 86400) == "1H"
    assert ohlcv_candle_type_for_age_seconds(60 * 86400) == "1D"


def test_ath_high_from_ohlcv_items_returns_max_high() -> None:
    items = [
        {"h": 0.001, "unixTime": 1},
        {"h": 0.0025, "unixTime": 2},
        {"h": 0.0015, "unixTime": 3},
    ]
    assert ath_high_from_ohlcv_items(items) == 0.0025
