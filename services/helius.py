from typing import Any, Optional

import httpx
import structlog

from domain.metadata_image import (
    image_url_from_helius_asset,
    image_url_from_metadata_json,
    metadata_json_uri_from_asset,
    resolve_content_uri,
)
from domain.security_snapshot import SecuritySnapshot

log = structlog.get_logger()


class HeliusError(Exception):
    pass


class HeliusClient:
    def __init__(self, *, api_key: str, timeout_seconds: float) -> None:
        self._rpc_url = f"https://mainnet.helius-rpc.com/?api-key={api_key}"
        self._timeout = timeout_seconds

    async def fetch_token_security(self, mint: str) -> SecuritySnapshot:
        try:
            account_info, largest = await self._rpc_batch(
                [
                    ("getAccountInfo", [mint, {"encoding": "jsonParsed"}]),
                    ("getTokenLargestAccounts", [mint]),
                ]
            )
        except Exception as exc:
            log.warning("helius_security_failed", mint=mint, error=str(exc))
            raise HeliusError from exc

        return _parse_security(account_info, largest)

    async def fetch_token_image_url(self, mint: str) -> Optional[str]:
        try:
            asset = await self._rpc_call(
                "getAsset",
                {"id": mint, "displayOptions": {"showFungible": True}},
            )
        except Exception as exc:
            log.warning("helius_get_asset_failed", mint=mint, error=str(exc))
            raise HeliusError from exc

        if not asset:
            return None

        image = image_url_from_helius_asset(asset)
        if image:
            return image

        json_uri = metadata_json_uri_from_asset(asset)
        if not json_uri:
            return None

        return await self._fetch_image_from_metadata_uri(json_uri)

    async def _fetch_image_from_metadata_uri(self, json_uri: str) -> Optional[str]:
        fetch_url = resolve_content_uri(json_uri)
        if not fetch_url:
            return None

        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.get(fetch_url)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            log.warning("helius_metadata_json_failed", uri=json_uri, error=str(exc))
            return None

        return image_url_from_metadata_json(payload)

    async def _rpc_call(self, method: str, params: Any) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                self._rpc_url,
                json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
            )
            response.raise_for_status()
            body = response.json()

        if body.get("error"):
            raise HeliusError(str(body["error"]))
        return body.get("result")

    async def _rpc_batch(
        self,
        calls: list[tuple[str, list[Any]]],
    ) -> list[Any]:
        payload = [
            {"jsonrpc": "2.0", "id": idx, "method": method, "params": params}
            for idx, (method, params) in enumerate(calls, start=1)
        ]
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(self._rpc_url, json=payload)
            response.raise_for_status()
            body = response.json()

        if not isinstance(body, list):
            body = [body]

        results: list[Any] = []
        for entry in sorted(body, key=lambda item: item.get("id", 0)):
            if entry.get("error"):
                raise HeliusError(str(entry["error"]))
            results.append(entry.get("result"))

        return results


def _parse_security(account_info: Any, largest_result: Any) -> SecuritySnapshot:
    mint_renounced: Optional[bool] = None
    freeze_renounced: Optional[bool] = None
    supply_ui: Optional[str] = None
    supply_amount: Optional[float] = None

    parsed = _parse_mint_account(account_info)
    if parsed:
        mint_renounced = parsed.get("mint_renounced")
        freeze_renounced = parsed.get("freeze_renounced")
        supply_amount = parsed.get("supply_amount")
        supply_ui = parsed.get("supply_ui")

    top10_pct: Optional[float] = None
    top_accounts = _extract_largest_accounts(largest_result)
    if supply_amount and top_accounts:
        top10_total = sum(amount for _, amount in top_accounts[:10])
        top10_pct = (top10_total / supply_amount) * 100 if supply_amount else None

    return SecuritySnapshot(
        mint_renounced=mint_renounced,
        freeze_renounced=freeze_renounced,
        top10_holder_pct=top10_pct,
        holder_count=None,
        supply_ui=supply_ui,
    )


def _parse_mint_account(account_info: Any) -> Optional[dict[str, Any]]:
    if not isinstance(account_info, dict) or account_info.get("value") is None:
        return None

    value = account_info["value"]
    data = value.get("data") or {}
    parsed = data.get("parsed") or {}
    if parsed.get("type") != "mint":
        return None

    info = parsed.get("info") or {}
    mint_authority = info.get("mintAuthority")
    freeze_authority = info.get("freezeAuthority")

    supply_raw = info.get("supply")
    decimals = info.get("decimals")
    supply_amount: Optional[float] = None
    supply_ui: Optional[str] = None

    if supply_raw is not None and decimals is not None:
        try:
            supply_amount = int(supply_raw) / (10 ** int(decimals))
            supply_ui = _format_supply_amount(supply_amount)
        except (TypeError, ValueError):
            pass

    return {
        "mint_renounced": mint_authority is None,
        "freeze_renounced": freeze_authority is None,
        "supply_amount": supply_amount,
        "supply_ui": supply_ui,
    }


def _format_supply_amount(amount: float) -> str:
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.0f}B"
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.0f}M"
    if amount >= 1_000:
        return f"{amount / 1_000:.0f}K"
    return f"{amount:.0f}"


def _extract_largest_accounts(result: Any) -> list[tuple[str, float]]:
    if not isinstance(result, dict):
        return []
    value = result.get("value") or []
    accounts: list[tuple[str, float]] = []
    for row in value:
        address = row.get("address")
        ui_amount = row.get("uiAmount")
        if address is None or ui_amount is None:
            continue
        try:
            accounts.append((str(address), float(ui_amount)))
        except (TypeError, ValueError):
            continue
    return accounts
