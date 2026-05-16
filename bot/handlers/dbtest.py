from telegram import Update
from telegram.ext import ContextTypes

from config.settings import get_settings
from db.queries import ping_database
from db.session import create_engine, create_session_factory


async def dbtest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    settings = get_settings()
    if not settings.database_url:
        await update.message.reply_text("DATABASE_URL is not set in .env")
        return

    engine = create_engine(settings)
    try:
        session_factory = create_session_factory(engine)
        async with session_factory() as session:
            connected = await ping_database(session)
    except Exception as exc:
        await update.message.reply_text(f"DB error: {type(exc).__name__}")
        return
    finally:
        await engine.dispose()

    if connected:
        await update.message.reply_text("DB connected")
    else:
        await update.message.reply_text("DB error")
