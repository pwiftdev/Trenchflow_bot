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
        url = f"{self._base_url}/tokens/v1/{chain_id}/{mint}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            log.warning("dexscreener_http_error", status=exc.response.status_code, mint=mint)
            raise DexScreenerError from exc
        except httpx.HTTPError as exc:
            log.warning("dexscreener_request_failed", mint=mint, error=str(exc))
            raise DexScreenerError from exc

        if not isinstance(payload, list) or not payload:
            raise TokenNotFoundError(mint)

        pair = _select_best_pair(payload, mint)
        if pair is None:
            raise TokenNotFoundError(mint)

        return _pair_to_snapshot(pair, mint)


def _select_best_pair(pairs: list[dict[str, Any]], mint: str) -> Optional[dict[str, Any]]:
    base_matches = [
        pair
        for pair in pairs
        if (pair.get("baseToken") or {}).get("address") == mint
    ]
    if base_matches:
        return max(
            base_matches,
            key=lambda pair: float((pair.get("liquidity") or {}).get("usd") or 0),
        )

    any_matches = [
        pair
        for pair in pairs
        if (pair.get("baseToken") or {}).get("address") == mint
        or (pair.get("quoteToken") or {}).get("address") == mint
    ]
    if any_matches:
        return max(
            any_matches,
            key=lambda pair: float((pair.get("liquidity") or {}).get("usd") or 0),
        )

    return max(pairs, key=lambda pair: float((pair.get("liquidity") or {}).get("usd") or 0))


def _pair_to_snapshot(pair: dict[str, Any], mint: str) -> TokenSnapshot:
    base = pair.get("baseToken") or {}
    quote = pair.get("quoteToken") or {}
    token = base if base.get("address") == mint else quote

    info = pair.get("info") or {}
    websites: list[tuple[str, str]] = []
    for site in info.get("websites") or []:
        site_url = site.get("url")
        if site_url:
            label = site.get("label") or "Website"
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

    return TokenSnapshot(
        mint=mint,
        symbol=token.get("symbol"),
        name=token.get("name"),
        price_usd=_to_float(pair.get("priceUsd")),
        market_cap=_to_float(pair.get("marketCap")),
        fdv=_to_float(pair.get("fdv")),
        liquidity_usd=_to_float(liquidity.get("usd")),
        volume_h24=_to_float(volume.get("h24")),
        price_change_h24=_to_float(price_change.get("h24")),
        dex_id=pair.get("dexId"),
        pair_url=pair.get("url"),
        image_url=info.get("imageUrl"),
        websites=websites,
        socials=socials,
    )


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
