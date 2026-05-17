import structlog
from telegram import Update
from telegram.ext import ContextTypes

from bot.filters import message_text
from bot.handlers.scan import run_scan
from domain.ca import extract_solana_mint_from_text

log = structlog.get_logger()


async def ca_detect_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None:
        return

    user = update.effective_user
    if user is not None and user.is_bot:
        return

    chat = update.effective_chat
    if chat is None or chat.type == "channel":
        return

    text = message_text(message)
    if not text:
        return

    mint = extract_solana_mint_from_text(text)
    if mint is None:
        return

    log.info("ca_detect_triggered", mint=mint, chat_id=chat.id, chat_type=chat.type)
    await run_scan(update, context, mint)
