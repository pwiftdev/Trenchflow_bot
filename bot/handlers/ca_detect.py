from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.scan import run_scan
from domain.ca import extract_solana_mint_from_text


async def ca_detect_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or not update.message.text:
        return

    user = update.effective_user
    if user is not None and user.is_bot:
        return

    chat = update.effective_chat
    if chat is None or chat.type == "channel":
        return

    mint = extract_solana_mint_from_text(update.message.text)
    if mint is None:
        return

    await run_scan(update, context, mint)
