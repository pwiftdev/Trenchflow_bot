import structlog
from telegram import Update
from telegram.ext import ContextTypes

from config.settings import get_settings

log = structlog.get_logger()


async def founderstest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    settings = get_settings()
    if settings.founders_chat_id is None:
        await update.message.reply_text("FOUNDERS_CHAT_ID is not set in .env")
        return

    bot = context.bot
    chat_id = settings.founders_chat_id
    text = (
        "Trenchflow alpha feed test\n"
        "If you see this, the bot can post to this chat."
    )
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except Exception as exc:
        log.warning("founderstest_send_failed", chat_id=chat_id, error=str(exc))
        await update.message.reply_text(f"Send failed: {exc}")
        return

    await update.message.reply_text(f"Sent test message to founders chat ({chat_id}).")
