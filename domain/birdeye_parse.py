"""Pure mapping from Birdeye API payloads to domain models."""

from typing import Any, Optional

from domain import explorer_links
from domain.security_snapshot import SecuritySnapshot
from domain.token_snapshot import TokenSnapshot


def overview_to_snapshot(data: dict[str, Any], mint: str) -> TokenSnapshot:
    extensions = data.get("extensions") or {}
    socials = _extensions_to_socials(extensions)
    websites = _extensions_to_websites(extensions)

    return TokenSnapshot(
        mint=mint,
        symbol=_str_or_none(data.get("symbol")),
        name=_str_or_none(data.get("name")),
        price_usd=_to_float(data.get("price")),
        market_cap=_to_float(data.get("marketCap")),
        fdv=_to_float(data.get("fdv")),
        liquidity_usd=_to_float(data.get("liquidity")),
        volume_h24=_to_float(data.get("v24hUSD")),
        price_change_h1=_to_float(data.get("priceChange1hPercent")),
        price_change_h24=_to_float(data.get("priceChange24hPercent")),
        txns_h1_buys=_to_int(data.get("buy1h")),
        txns_h1_sells=_to_int(data.get("sell1h")),
        pair_created_at_ms=None,
        dex_id=None,
        labels=[],
        pair_url=explorer_links.birdeye_token_url(mint),
        image_url=_normalize_https(data.get("logoURI")),
        header_image_url=None,
        open_graph_url=None,
        websites=websites,
        socials=socials,
    )


def security_from_birdeye(
    data: dict[str, Any],
    *,
    holder_count: Optional[int] = None,
    top10_holder_pct: Optional[float] = None,
) -> SecuritySnapshot:
    top10 = top10_holder_pct
    if top10 is None:
        top10 = _to_float(data.get("top10HolderPercent"))
        if top10 is not None:
            top10 = _holder_percent_display(top10)

    supply = _to_float(data.get("totalSupply"))
    supply_ui = _format_supply_ui(supply) if supply is not None else None

    return SecuritySnapshot(
        mint_renounced=None,
        freeze_renounced=_freeze_renounced(data),
        top10_holder_pct=top10,
        holder_count=holder_count,
        supply_ui=supply_ui,
        dev_sold_label=_dev_holder_label(_to_float(data.get("creatorPercentage"))),
    )


def merge_security(
    primary: Optional[SecuritySnapshot],
    supplement: Optional[SecuritySnapshot],
) -> Optional[SecuritySnapshot]:
    """Prefer Birdeye fields; fill gaps from Helius (e.g. mint authority)."""
    if primary is None:
        return supplement
    if supplement is None:
        return primary

    return SecuritySnapshot(
        mint_renounced=primary.mint_renounced
        if primary.mint_renounced is not None
        else supplement.mint_renounced,
        freeze_renounced=primary.freeze_renounced
        if primary.freeze_renounced is not None
        else supplement.freeze_renounced,
        top10_holder_pct=primary.top10_holder_pct
        if primary.top10_holder_pct is not None
        else supplement.top10_holder_pct,
        holder_count=primary.holder_count
        if primary.holder_count is not None
        else supplement.holder_count,
        supply_ui=primary.supply_ui if primary.supply_ui is not None else supplement.supply_ui,
        fresh_1d_pct=primary.fresh_1d_pct or supplement.fresh_1d_pct,
        fresh_7d_pct=primary.fresh_7d_pct or supplement.fresh_7d_pct,
        dev_sold_label=primary.dev_sold_label or supplement.dev_sold_label,
    )


def holder_count_from_overview(data: dict[str, Any]) -> Optional[int]:
    return _to_int(data.get("holder"))


def total_supply_from_overview(data: dict[str, Any]) -> Optional[float]:
    supply = _to_float(data.get("circulatingSupply"))
    if supply is None:
        supply = _to_float(data.get("totalSupply"))
    return supply


def total_supply_from_security(data: dict[str, Any]) -> Optional[float]:
    return _to_float(data.get("totalSupply"))


def creation_time_ms_from_security(data: dict[str, Any]) -> Optional[int]:
    unix = _to_int(data.get("creationTime"))
    if unix is not None:
        return unix * 1000
    return None


def _freeze_renounced(data: dict[str, Any]) -> Optional[bool]:
    freeze_authority = data.get("freezeAuthority")
    freezeable = data.get("freezeable")
    if freeze_authority is None:
        return True
    if freezeable is False:
        return True
    if freezeable is True or freeze_authority:
        return False
    return None


def _dev_holder_label(creator_pct: Optional[float]) -> Optional[str]:
    if creator_pct is None:
        return None
    if creator_pct < 0.01:
        return "🟢"
    pct = creator_pct if creator_pct >= 1 else creator_pct * 100
    return f"🔴{pct:.1f}%"


def _holder_percent_display(value: float) -> float:
    if 0 <= value <= 1:
        return value * 100.0
    return value


def _extensions_to_socials(extensions: dict[str, Any]) -> list[tuple[str, str]]:
    socials: list[tuple[str, str]] = []
    for key in ("twitter", "telegram", "discord", "medium"):
        url = _normalize_https(extensions.get(key))
        if url:
            socials.append((key, url))
    return socials


def _extensions_to_websites(extensions: dict[str, Any]) -> list[tuple[str, str]]:
    url = _normalize_https(extensions.get("website"))
    if url:
        return [("Website", url)]
    return []


def _format_supply_ui(amount: float) -> str:
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.0f}B"
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.0f}M"
    if amount >= 1_000:
        return f"{amount / 1_000:.0f}K"
    return f"{amount:.0f}"


def _str_or_none(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_https(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned if cleaned.startswith("https://") else None


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def ohlcv_candle_type_for_age_seconds(age_seconds: int) -> str:
    """Pick OHLCV granularity so we stay within Birdeye's 1000-candle cap."""
    if age_seconds <= 2 * 86400:
        return "15m"
    if age_seconds <= 45 * 86400:
        return "1H"
    return "1D"


def ath_high_from_ohlcv_items(
    items: list[dict[str, Any]],
    *,
    use_scaled: bool = False,
) -> Optional[float]:
    """All-time high USD from OHLCV highs ([Birdeye OHLCV](https://docs.birdeye.so/reference/get-defi-ohlcv))."""
    peak: Optional[float] = None
    high_key = "scaledH" if use_scaled else "h"
    for row in items:
        if not isinstance(row, dict):
            continue
        high = _to_float(row.get(high_key))
        if high is None:
            high = _to_float(row.get("h"))
        if high is None:
            continue
        peak = high if peak is None else max(peak, high)
    return peak
