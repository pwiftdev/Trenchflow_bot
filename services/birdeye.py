import time
from typing import Any, Optional

import httpx
import structlog

from domain.birdeye_parse import ath_high_from_ohlcv_items, ohlcv_candle_type_for_age_seconds

log = structlog.get_logger()


class BirdeyeError(Exception):
    pass


class BirdeyeAuthError(BirdeyeError):
    pass


class TokenNotFoundError(BirdeyeError):
    pass


class BirdeyeClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        chain: str,
        timeout_seconds: float,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._chain = chain
        self._timeout = timeout_seconds
        self._http: Optional[httpx.AsyncClient] = None

    async def aclose(self) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    def _client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(timeout=self._timeout)
        return self._http

    async def fetch_token_overview(self, mint: str) -> dict[str, Any]:
        return await self._fetch_data("/defi/token_overview", mint)

    async def fetch_token_security(self, mint: str) -> dict[str, Any]:
        return await self._fetch_data("/defi/token_security", mint)

    async def fetch_token_holders(
        self,
        mint: str,
        *,
        limit: int = 100,
        offset: int = 0,
        ui_amount_mode: str = "raw",
    ) -> list[dict[str, Any]]:
        data = await self._fetch_data(
            "/defi/v3/token/holder",
            mint,
            extra_params={
                "limit": limit,
                "offset": offset,
                "ui_amount_mode": ui_amount_mode,
            },
        )
        items = data.get("items")
        if not isinstance(items, list):
            return []
        return [item for item in items if isinstance(item, dict)]

    async def fetch_holder_profile(
        self,
        mint: str,
        *,
        interval: str = "1h",
        ui_amount_mode: str = "raw",
    ) -> dict[str, Any]:
        return await self._fetch_data(
            "/token/v1/holder-profile",
            mint,
            address_param="token_address",
            extra_params={
                "interval": interval,
                "ui_amount_mode": ui_amount_mode,
                "include_zero_balance": "true",
            },
        )

    async def fetch_token_ath_usd(
        self,
        mint: str,
        *,
        created_at_unix: Optional[int] = None,
        lookback_seconds: int = 90 * 86400,
    ) -> Optional[float]:
        now = int(time.time())
        if created_at_unix and created_at_unix > 0:
            time_from = created_at_unix
            age_seconds = max(0, now - created_at_unix)
        else:
            age_seconds = lookback_seconds
            time_from = now - lookback_seconds

        candle_type = ohlcv_candle_type_for_age_seconds(age_seconds)
        data = await self._fetch_data(
            "/defi/ohlcv",
            mint,
            extra_params={
                "type": candle_type,
                "currency": "usd",
                "time_from": str(time_from),
                "time_to": str(now),
            },
        )
        items = data.get("items") or []
        if not isinstance(items, list) or not items:
            log.warning("birdeye_ohlcv_empty", mint=mint, candle_type=candle_type)
            return None

        use_scaled = bool(data.get("isScaledUiToken"))
        return ath_high_from_ohlcv_items(items, use_scaled=use_scaled)

    async def _fetch_data(
        self,
        path: str,
        mint: str,
        *,
        address_param: str = "address",
        extra_params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        headers = {
            "X-API-KEY": self._api_key,
            "x-chain": self._chain,
            "accept": "application/json",
        }
        params: dict[str, Any] = {address_param: mint}
        if extra_params:
            params.update(extra_params)

        try:
            response = await self._client().get(url, headers=headers, params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            detail = _response_message(exc.response)
            log.warning(
                "birdeye_http_error",
                path=path,
                status=status,
                mint=mint,
                detail=detail,
            )
            if status == 404:
                raise TokenNotFoundError(mint) from exc
            if status in (401, 403):
                raise BirdeyeAuthError(
                    "Birdeye rejected the API key"
                    + (f" ({detail})" if detail else "")
                    + ". Use a key from bds.birdeye.so → Security; check IP whitelist."
                ) from exc
            raise BirdeyeError from exc
        except httpx.HTTPError as exc:
            log.warning("birdeye_request_failed", path=path, mint=mint, error=str(exc))
            raise BirdeyeError from exc

        return _parse_success_payload(payload, mint=mint, path=path)


def _response_message(response: httpx.Response) -> Optional[str]:
    try:
        body = response.json()
    except ValueError:
        return None
    if isinstance(body, dict):
        message = body.get("message")
        if message:
            return str(message)
    return None


def _parse_success_payload(payload: Any, *, mint: str, path: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise BirdeyeError(f"Unexpected Birdeye response for {mint}")

    if not payload.get("success"):
        message = payload.get("message") or "Birdeye request failed"
        log.warning("birdeye_api_error", path=path, mint=mint, message=message)
        if "not found" in str(message).lower():
            raise TokenNotFoundError(mint)
        raise BirdeyeError(message)

    data = payload.get("data")
    if not isinstance(data, dict) or not data:
        raise TokenNotFoundError(mint)

    return data
