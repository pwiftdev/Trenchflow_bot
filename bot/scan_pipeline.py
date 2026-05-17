"""Fetch and compose scan card data (shared by /scan and refresh)."""

import asyncio
import dataclasses
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from telegram import Update

from bot.scan_context import build_first_call_line, build_scan_meta
from config.settings import get_settings
from domain.birdeye_parse import (
    creation_time_ms_from_security,
    holder_count_from_overview,
    merge_security,
    overview_to_snapshot,
    security_from_birdeye,
)
from domain.scan_card import ScanMeta, format_scan_card
from domain.security_snapshot import SecuritySnapshot
from domain.token_snapshot import TokenSnapshot
from domain.trench_alert import TrenchAlert, holder_profile_from_birdeye
from services.birdeye import (
    BirdeyeClient,
    BirdeyeError,
    TokenNotFoundError as BirdeyeTokenNotFound,
)

__all__ = [
    "BirdeyeError",
    "BirdeyeTokenNotFound",
    "ScanResult",
    "build_scan_result",
    "birdeye_client",
]
from services.dexscreener import DexScreenerClient
from services.helius import HeliusClient, HeliusError


@dataclass(frozen=True)
class ScanResult:
    snapshot: TokenSnapshot
    security: Optional[SecuritySnapshot]
    trench_alert: Optional[TrenchAlert]
    meta: ScanMeta
    caption: str


def birdeye_client() -> BirdeyeClient:
    settings = get_settings()
    if not settings.birdeye_api_key:
        raise BirdeyeError("BIRDEYE_API_KEY is not configured")
    return BirdeyeClient(
        api_key=settings.birdeye_api_key,
        base_url=settings.birdeye_base_url,
        chain=settings.birdeye_chain,
        timeout_seconds=settings.birdeye_timeout_seconds,
    )


def dexscreener_client() -> DexScreenerClient:
    settings = get_settings()
    return DexScreenerClient(
        base_url=settings.dexscreener_base_url,
        timeout_seconds=settings.dexscreener_timeout_seconds,
    )


def _helius_client() -> Optional[HeliusClient]:
    settings = get_settings()
    if not settings.helius_api_key:
        return None
    return HeliusClient(
        api_key=settings.helius_api_key,
        timeout_seconds=settings.helius_timeout_seconds,
    )


async def _fetch_helius_security(mint: str) -> Optional[SecuritySnapshot]:
    client = _helius_client()
    if client is None:
        return None
    try:
        return await client.fetch_token_security(mint)
    except HeliusError:
        return None


async def _fetch_metadata_image(mint: str) -> Optional[str]:
    client = _helius_client()
    if client is None:
        return None
    try:
        return await client.fetch_token_image_url(mint)
    except HeliusError:
        return None


def _apply_token_age(
    snapshot: TokenSnapshot,
    *,
    overview_data: dict[str, Any],
    security_data: dict[str, Any],
) -> TokenSnapshot:
    created_ms = creation_time_ms_from_security(security_data)
    if created_ms is None:
        created_ms = creation_time_ms_from_security(overview_data)
    if created_ms is None:
        return snapshot
    return dataclasses.replace(snapshot, pair_created_at_ms=created_ms)


async def build_scan_result(update: Update, mint: str) -> ScanResult:
    settings = get_settings()
    birdeye = birdeye_client()
    dex_client = dexscreener_client()

    (
        overview_data,
        security_data,
        holder_profile_data,
        helius_security,
        metadata_image,
        dex_orders,
    ) = await asyncio.gather(
        birdeye.fetch_token_overview(mint),
        birdeye.fetch_token_security(mint),
        birdeye.fetch_holder_profile(
            mint,
            interval=settings.birdeye_holder_profile_interval,
        ),
        _fetch_helius_security(mint),
        _fetch_metadata_image(mint),
        dex_client.fetch_token_orders(settings.solana_chain_id, mint),
    )

    snapshot = overview_to_snapshot(overview_data, mint)
    snapshot = _apply_token_age(
        snapshot,
        overview_data=overview_data,
        security_data=security_data,
    )

    created_unix = (
        snapshot.pair_created_at_ms // 1000 if snapshot.pair_created_at_ms is not None else None
    )
    ath_price_usd = await birdeye.fetch_token_ath_usd(
        mint,
        created_at_unix=created_unix,
        lookback_seconds=settings.birdeye_ath_lookback_days * 86400,
    )

    birdeye_security = security_from_birdeye(
        security_data,
        holder_count=holder_count_from_overview(overview_data),
    )
    security = merge_security(birdeye_security, helius_security)
    trench_alert = holder_profile_from_birdeye(holder_profile_data)

    snapshot = dataclasses.replace(
        snapshot,
        metadata_image_url=metadata_image or snapshot.metadata_image_url,
        dex_profile_paid=dex_orders.profile_paid,
        dex_boost_amount_total=dex_orders.boost_amount_total or None,
        ath_price_usd=ath_price_usd,
    )

    scanned_at = datetime.now(timezone.utc)
    first_call_line = await build_first_call_line(update, mint=mint, snapshot=snapshot)
    meta = build_scan_meta(
        update,
        scanned_at=scanned_at,
        snapshot=snapshot,
        first_call_line=first_call_line,
    )
    caption = format_scan_card(snapshot, meta, security, trench_alert=trench_alert)
    if len(caption) > 1024:
        caption = caption[:1020] + "…"

    return ScanResult(
        snapshot=snapshot,
        security=security,
        trench_alert=trench_alert,
        meta=meta,
        caption=caption,
    )
