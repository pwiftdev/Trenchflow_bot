from domain.scan_media import photo_url_candidates
from domain.token_snapshot import TokenSnapshot


def _snapshot(**kwargs) -> TokenSnapshot:
    base = dict(
        mint="Mint1111111111111111111111111111111111111",
        symbol="T",
        name="Test",
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
    base.update(kwargs)
    return TokenSnapshot(**base)


def test_photo_candidates_skip_gif_header_for_icon_first() -> None:
    snapshot = _snapshot(
        header_image_url="https://cdn.example.com/banner.gif?format=gif",
        image_url="https://cdn.example.com/icon.png",
    )
    assert photo_url_candidates(snapshot) == [
        "https://cdn.example.com/icon.png",
        "https://cdn.example.com/banner.gif?format=gif",
    ]


def test_photo_candidates_header_then_icon() -> None:
    snapshot = _snapshot(
        header_image_url="https://cdn.example.com/banner.png",
        image_url="https://cdn.example.com/icon.png",
    )
    assert photo_url_candidates(snapshot) == [
        "https://cdn.example.com/banner.png",
        "https://cdn.example.com/icon.png",
    ]


def test_photo_candidates_dedupes_identical_urls() -> None:
    url = "https://cdn.example.com/same.png"
    snapshot = _snapshot(header_image_url=url, image_url=url)
    assert photo_url_candidates(snapshot) == [url]
