from telegram import Update
from telegram.ext import ContextTypes


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text("pong")
