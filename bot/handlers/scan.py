import asyncio
import dataclasses
from datetime import datetime, timezone
from typing import Any, Optional

import structlog
from telegram import Update
from telegram.ext import ContextTypes

from bot.alpha_notify import notify_founders_scan
from bot.scan_context import build_first_call_line, build_scan_meta, record_scan_event
from bot.scan_keyboard import build_scan_keyboard
from bot.scan_reply import reply_scan_card
from config.settings import get_settings
from domain.birdeye_parse import (
    creation_time_ms_from_security,
    holder_count_from_overview,
    merge_security,
    overview_to_snapshot,
    security_from_birdeye,
)
from domain.ca import is_valid_solana_address
from domain.scan_card import format_scan_card
from domain.security_snapshot import SecuritySnapshot
from domain.token_snapshot import TokenSnapshot
from services.birdeye import (
    BirdeyeClient,
    BirdeyeError,
    TokenNotFoundError as BirdeyeTokenNotFound,
)
from services.dexscreener import DexScreenerClient, DexScreenerError, TokenNotFoundError as DexTokenNotFound
from services.helius import HeliusClient, HeliusError

log = structlog.get_logger()


def _birdeye_client() -> Optional[BirdeyeClient]:
    settings = get_settings()
    if not settings.birdeye_api_key:
        return None
    return BirdeyeClient(
        api_key=settings.birdeye_api_key,
        base_url=settings.birdeye_base_url,
        chain=settings.birdeye_chain,
        timeout_seconds=settings.birdeye_timeout_seconds,
    )


def _dexscreener_client() -> DexScreenerClient:
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


async def _fetch_birdeye_overview(
    client: BirdeyeClient,
    mint: str,
) -> Optional[dict[str, Any]]:
    try:
        return await client.fetch_token_overview(mint)
    except BirdeyeTokenNotFound:
        return None
    except BirdeyeError as exc:
        log.warning("birdeye_overview_failed", mint=mint, error=str(exc))
        return None


async def _fetch_birdeye_security(
    client: BirdeyeClient,
    mint: str,
) -> Optional[dict[str, Any]]:
    try:
        return await client.fetch_token_security(mint)
    except BirdeyeError as exc:
        log.warning("birdeye_security_failed", mint=mint, error=str(exc))
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


async def _snapshot_from_dex(
    dex_client: DexScreenerClient,
    chain_id: str,
    mint: str,
) -> TokenSnapshot:
    return await dex_client.fetch_token_snapshot(chain_id, mint)


async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if not context.args:
        await update.message.reply_text("Usage: /scan <contract address>")
        return

    mint = context.args[0].strip()
    if not is_valid_solana_address(mint):
        await update.message.reply_text("That doesn't look like a valid Solana contract address.")
        return

    settings = get_settings()
    dex_client = _dexscreener_client()
    birdeye = _birdeye_client()

    helius_security, metadata_image, dex_orders = await asyncio.gather(
        _fetch_helius_security(mint),
        _fetch_metadata_image(mint),
        dex_client.fetch_token_orders(settings.solana_chain_id, mint),
    )

    overview_data: Optional[dict[str, Any]] = None
    security_data: Optional[dict[str, Any]] = None
    if birdeye is not None:
        overview_data, security_data = await asyncio.gather(
            _fetch_birdeye_overview(birdeye, mint),
            _fetch_birdeye_security(birdeye, mint),
        )

    snapshot: Optional[TokenSnapshot] = None
    if overview_data is not None:
        snapshot = overview_to_snapshot(overview_data, mint)
        snapshot = _apply_token_age(
            snapshot,
            overview_data=overview_data,
            security_data=security_data or {},
        )

    if snapshot is None:
        try:
            snapshot = await _snapshot_from_dex(dex_client, settings.solana_chain_id, mint)
        except DexTokenNotFound:
            await update.message.reply_text(
                "Token not found on Birdeye or DexScreener yet. It may be too new or illiquid."
            )
            return
        except DexScreenerError:
            await update.message.reply_text(
                "Couldn't load market data right now. Try again in a moment."
            )
            return

    if overview_data is not None and security_data is not None:
        birdeye_security = security_from_birdeye(
            security_data,
            holder_count=holder_count_from_overview(overview_data),
        )
        security = merge_security(birdeye_security, helius_security)
    elif security_data is not None:
        security = merge_security(
            security_from_birdeye(security_data, holder_count=None),
            helius_security,
        )
    else:
        security = helius_security

    snapshot = dataclasses.replace(
        snapshot,
        metadata_image_url=metadata_image or snapshot.metadata_image_url,
        dex_profile_paid=dex_orders.profile_paid,
        dex_boost_amount_total=dex_orders.boost_amount_total or None,
    )

    scanned_at = datetime.now(timezone.utc)
    first_call_line = await build_first_call_line(update, mint=mint, snapshot=snapshot)
    meta = build_scan_meta(
        update,
        scanned_at=scanned_at,
        snapshot=snapshot,
        first_call_line=first_call_line,
    )
    caption = format_scan_card(snapshot, meta, security)
    if len(caption) > 1024:
        caption = caption[:1020] + "…"

    keyboard = build_scan_keyboard(snapshot)

    await record_scan_event(update, mint=mint, scanned_at=scanned_at, snapshot=snapshot)
    await notify_founders_scan(
        context.bot,
        update=update,
        snapshot=snapshot,
        meta=meta,
        scanned_at=scanned_at,
    )

    await reply_scan_card(
        update.message,
        caption=caption,
        keyboard=keyboard,
        snapshot=snapshot,
    )
