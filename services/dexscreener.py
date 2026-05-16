from typing import Any, Optional

import httpx
import structlog

from domain.token_snapshot import TokenSnapshot

log = structlog.get_logger()


class DexScreenerError(Exception):
    pass


class TokenNotFoundError(DexScreenerError):
    pass


class DexScreenerClient:
    def __init__(self, *, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def fetch_token_snapshot(self, chain_id: str, mint: str) -> TokenSnapshot:
        """Load all pools for a mint and pick the best pair (highest liquidity).

        We use token-pairs/v1, not tokens/v1: for pump.fun graduates, tokens/v1 often
        returns only the bonding-curve pool (~stale MC) while pumpswap/raydium has the
        live price and market cap.
        """
        pairs = await self._fetch_pairs(chain_id, mint)
        if not pairs:
            raise TokenNotFoundError(mint)

        pair = _select_best_pair(pairs, mint)
        if pair is None:
            raise TokenNotFoundError(mint)

        return _pair_to_snapshot(pair, mint)

    async def _fetch_pairs(self, chain_id: str, mint: str) -> list[dict[str, Any]]:
        endpoints = (
            f"{self._base_url}/token-pairs/v1/{chain_id}/{mint}",
            f"{self._base_url}/tokens/v1/{chain_id}/{mint}",
        )
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                for url in endpoints:
                    response = await client.get(url)
                    response.raise_for_status()
                    payload = response.json()
                    if isinstance(payload, list) and payload:
                        return payload
        except httpx.HTTPStatusError as exc:
            log.warning("dexscreener_http_error", status=exc.response.status_code, mint=mint)
            raise DexScreenerError from exc
        except httpx.HTTPError as exc:
            log.warning("dexscreener_request_failed", mint=mint, error=str(exc))
            raise DexScreenerError from exc

        return []


def _select_best_pair(pairs: list[dict[str, Any]], mint: str) -> Optional[dict[str, Any]]:
    # Market cap and priceUsd are for the base token — only use pools where our mint is base.
    base_matches = [
        pair
        for pair in pairs
        if (pair.get("baseToken") or {}).get("address") == mint
    ]
    if not base_matches:
        return None

    return max(base_matches, key=_pair_rank_score)


def _pair_rank_score(pair: dict[str, Any]) -> tuple[float, float, float]:
    liquidity = float((pair.get("liquidity") or {}).get("usd") or 0)
    volume_h24 = float((pair.get("volume") or {}).get("h24") or 0)
    market_cap = float(pair.get("marketCap") or 0)
    return (liquidity, volume_h24, market_cap)


def _pair_to_snapshot(pair: dict[str, Any], mint: str) -> TokenSnapshot:
    base = pair.get("baseToken") or {}
    quote = pair.get("quoteToken") or {}
    token = base if base.get("address") == mint else quote

    info = pair.get("info") or {}
    websites: list[tuple[str, str]] = []
    for site in info.get("websites") or []:
        site_url = site.get("url")
        if site_url:
            label = site.get("label") or "Web"
            websites.append((str(label), str(site_url)))

    socials: list[tuple[str, str]] = []
    for social in info.get("socials") or []:
        social_url = social.get("url")
        if social_url:
            label = social.get("type") or social.get("platform") or "Social"
            socials.append((str(label), str(social_url)))

    volume = pair.get("volume") or {}
    price_change = pair.get("priceChange") or {}
    liquidity = pair.get("liquidity") or {}
    txns_h1 = (pair.get("txns") or {}).get("h1") or {}
    boosts = pair.get("boosts") or {}

    labels = [str(label) for label in (pair.get("labels") or [])]

    change_h24 = _to_float(price_change.get("h24"))
    if change_h24 is None:
        change_h24 = _to_float(price_change.get("h6"))

    return TokenSnapshot(
        mint=mint,
        symbol=token.get("symbol"),
        name=token.get("name"),
        price_usd=_to_float(pair.get("priceUsd")),
        market_cap=_to_float(pair.get("marketCap")),
        fdv=_to_float(pair.get("fdv")),
        liquidity_usd=_to_float(liquidity.get("usd")),
        volume_h24=_to_float(volume.get("h24")),
        price_change_h1=_to_float(price_change.get("h1")),
        price_change_h24=change_h24,
        txns_h1_buys=_to_int(txns_h1.get("buys")),
        txns_h1_sells=_to_int(txns_h1.get("sells")),
        pair_created_at_ms=_to_int(pair.get("pairCreatedAt")),
        dex_id=pair.get("dexId"),
        labels=labels,
        pair_url=pair.get("url"),
        image_url=_normalize_media_url(info.get("imageUrl")),
        header_image_url=_normalize_media_url(info.get("header")),
        open_graph_url=_normalize_media_url(info.get("openGraph")),
        websites=websites,
        socials=socials,
        boosts_active=_to_int(boosts.get("active")),
    )


def _normalize_media_url(value: Any) -> Optional[str]:
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
