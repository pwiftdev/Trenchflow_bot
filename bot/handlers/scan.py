import asyncio
from datetime import datetime, timezone
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from bot.scan_context import build_first_call_line, build_scan_meta, record_scan_event
from bot.scan_keyboard import build_scan_keyboard
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
        snapshot, security = await asyncio.gather(
            dex_client.fetch_token_snapshot(settings.solana_chain_id, mint),
            _fetch_security(mint),
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
    banner = snapshot.header_image_url or snapshot.image_url

    await record_scan_event(update, mint=mint, scanned_at=scanned_at)

    if banner:
        await update.message.reply_photo(
            photo=banner,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return

    await update.message.reply_text(
        caption,
        parse_mode="HTML",
        disable_web_page_preview=False,
        reply_markup=keyboard,
    )
