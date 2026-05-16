import asyncio
import dataclasses
from datetime import datetime, timezone
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from bot.alpha_notify import notify_founders_scan
from bot.scan_context import build_first_call_line, build_scan_meta, record_scan_event
from bot.scan_keyboard import build_scan_keyboard
from bot.scan_reply import reply_scan_card
from config.settings import get_settings
from domain.ca import is_valid_solana_address
from domain.scan_card import format_scan_card
from domain.security_snapshot import SecuritySnapshot
from services.dexscreener import DexScreenerClient, DexScreenerError, TokenNotFoundError
from services.helius import HeliusClient, HeliusError


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


async def _fetch_security(mint: str) -> Optional[SecuritySnapshot]:
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

    try:
        snapshot, security, metadata_image = await asyncio.gather(
            dex_client.fetch_token_snapshot(settings.solana_chain_id, mint),
            _fetch_security(mint),
            _fetch_metadata_image(mint),
        )
    except TokenNotFoundError:
        await update.message.reply_text(
            "Token not found on DexScreener yet. It may be too new or illiquid."
        )
        return
    except DexScreenerError:
        await update.message.reply_text(
            "Couldn't reach DexScreener right now. Try again in a moment."
        )
        return

    if metadata_image:
        snapshot = dataclasses.replace(snapshot, metadata_image_url=metadata_image)

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
