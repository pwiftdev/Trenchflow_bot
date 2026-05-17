from typing import Any, Optional

import httpx
import structlog

log = structlog.get_logger()


class BirdeyeError(Exception):
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

    async def fetch_token_overview(self, mint: str) -> dict[str, Any]:
        return await self._fetch_data("/defi/token_overview", mint)

    async def fetch_token_security(self, mint: str) -> dict[str, Any]:
        return await self._fetch_data("/defi/token_security", mint)

    async def _fetch_data(self, path: str, mint: str) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        headers = {
            "X-API-KEY": self._api_key,
            "x-chain": self._chain,
            "accept": "application/json",
        }
        params = {"address": mint}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            log.warning("birdeye_http_error", path=path, status=status, mint=mint)
            if status == 404:
                raise TokenNotFoundError(mint) from exc
            if status == 401:
                raise BirdeyeError("Invalid or missing Birdeye API key") from exc
            raise BirdeyeError from exc
        except httpx.HTTPError as exc:
            log.warning("birdeye_request_failed", path=path, mint=mint, error=str(exc))
            raise BirdeyeError from exc

        return _parse_success_payload(payload, mint=mint, path=path)


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
