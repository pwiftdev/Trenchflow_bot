from typing import Optional

from domain.token_snapshot import TokenSnapshot


def photo_url_candidates(snapshot: TokenSnapshot) -> list[str]:
    """URLs to try for Telegram send_photo, best first.

    DexScreener often sets ``info.header`` before the banner file is ready, or
    serves it as a GIF — ``reply_photo`` then fails and we must fall back to
    ``imageUrl`` (usually a square PNG/JPEG icon).
    """
    raw = (
        snapshot.header_image_url,
        snapshot.image_url,
        snapshot.open_graph_url,
    )
    seen: set[str] = set()
    still: list[str] = []
    animated: list[str] = []

    for url in raw:
        normalized = _normalize_https_url(url)
        if normalized is None or normalized in seen:
            continue
        seen.add(normalized)
        if _is_gif_url(normalized):
            animated.append(normalized)
        else:
            still.append(normalized)

    return still + animated


def _normalize_https_url(url: Optional[str]) -> Optional[str]:
    if not url or not isinstance(url, str):
        return None
    cleaned = url.strip()
    if not cleaned.startswith("https://"):
        return None
    return cleaned


def _is_gif_url(url: str) -> bool:
    path = url.split("?", 1)[0].lower()
    return path.endswith(".gif") or "/gif" in path or "format=gif" in url.lower()
