from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

from bot.alpha_notify import notify_founders_scan
from bot.scan_context import record_scan_event
from bot.scan_keyboard import build_scan_keyboard
from bot.scan_pipeline import (
    BirdeyeError,
    BirdeyeTokenNotFound,
    build_scan_result,
)
from bot.scan_reply import reply_scan_card
from config.settings import get_settings
from domain.ca import is_valid_solana_address


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
    if not settings.birdeye_api_key:
        await update.message.reply_text(
            "Birdeye is not configured yet. Add BIRDEYE_API_KEY to the server environment."
        )
        return

    try:
        result = await build_scan_result(update, mint)
    except BirdeyeTokenNotFound:
        await update.message.reply_text(
            "Token not found on Birdeye yet. It may be too new or not indexed."
        )
        return
    except BirdeyeError as exc:
        await update.message.reply_text(f"Birdeye error: {exc}")
        return

    scanned_at = datetime.now(timezone.utc)
    await record_scan_event(
        update,
        mint=mint,
        scanned_at=scanned_at,
        snapshot=result.snapshot,
    )
    await notify_founders_scan(
        context.bot,
        update=update,
        snapshot=result.snapshot,
        meta=result.meta,
        scanned_at=scanned_at,
    )

    delivered = await reply_scan_card(
        update.message,
        caption=result.caption,
        keyboard=build_scan_keyboard(mint),
        snapshot=result.snapshot,
    )
    if not delivered:
        await update.message.reply_text(
            "Scan data loaded but the card could not be posted. Check bot permissions or try again.",
        )
