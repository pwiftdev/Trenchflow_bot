from telegram.ext import Application, CommandHandler

from bot.handlers.ping import ping_command
from config.settings import Settings


def build_application(settings: Settings) -> Application:
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )
    application.add_handler(CommandHandler("ping", ping_command))
    return application
