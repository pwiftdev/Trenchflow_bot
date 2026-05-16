from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

from bot.scan_context import build_scan_meta, record_scan_event
from config.settings import get_settings
from domain.ca import is_valid_solana_address
from domain.scan_card import format_scan_card
from services.dexscreener import DexScreenerClient, DexScreenerError, TokenNotFoundError


def _dexscreener_client() -> DexScreenerClient:
    settings = get_settings()
    return DexScreenerClient(
        base_url=settings.dexscreener_base_url,
        timeout_seconds=settings.dexscreener_timeout_seconds,
    )


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
    client = _dexscreener_client()

    try:
        snapshot = await client.fetch_token_snapshot(settings.solana_chain_id, mint)
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
    meta = build_scan_meta(update, scanned_at=scanned_at)
    caption = format_scan_card(snapshot, meta)
    if len(caption) > 1024:
        caption = caption[:1020] + "…"

    await record_scan_event(update, mint=mint, scanned_at=scanned_at)

    if snapshot.image_url:
        await update.message.reply_photo(
            photo=snapshot.image_url,
            caption=caption,
            parse_mode="HTML",
        )
        return

    await update.message.reply_text(
        caption,
        parse_mode="HTML",
        disable_web_page_preview=False,
    )
