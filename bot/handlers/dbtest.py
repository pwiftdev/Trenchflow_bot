from telegram import Update
from telegram.ext import ContextTypes

from config.settings import get_settings
from db import runtime as db_runtime
from db.queries import ping_database


async def dbtest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    settings = get_settings()
    if not db_runtime.database_enabled(settings):
        await update.message.reply_text("DATABASE_URL is not set in .env")
        return

    try:
        async with db_runtime.session_factory()() as session:
            connected = await ping_database(session)
    except RuntimeError:
        await update.message.reply_text("Database pool not initialized — restart the bot.")
        return
    except Exception as exc:
        await update.message.reply_text(f"DB error: {type(exc).__name__}")
        return

    if connected:
        await update.message.reply_text("DB connected")
    else:
        await update.message.reply_text("DB error")
