from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    MessageHandler,
)

from bot.commands import register_bot_commands
from bot.filters import HAS_SOLANA_MINT
from bot.handlers.ca_detect import ca_detect_message
from bot.handlers.group_setup import on_bot_added_to_group
from bot.handlers.dbtest import dbtest_command
from bot.handlers.founderstest import founderstest_command
from bot.handlers.help import help_command
from bot.handlers.ping import ping_command
from bot.handlers.scan import scan_command
from bot.handlers.scan_callbacks import scan_callback
from bot.handlers.vpstest import vpstest_command
from bot.scan_keyboard import DELETE_CALLBACK, REFRESH_PREFIX
from config.settings import Settings


def build_application(settings: Settings) -> Application:
    async def post_init(application: Application) -> None:
        await register_bot_commands(application.bot, settings)

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .build()
    )
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("scan", scan_command))
    application.add_handler(MessageHandler(HAS_SOLANA_MINT, ca_detect_message))
    application.add_handler(
        ChatMemberHandler(on_bot_added_to_group, ChatMemberHandler.MY_CHAT_MEMBER),
    )
    application.add_handler(
        CallbackQueryHandler(scan_callback, pattern=f"^({DELETE_CALLBACK}|{REFRESH_PREFIX})")
    )
    application.add_handler(CommandHandler("ping", ping_command))
    application.add_handler(CommandHandler("vpstest", vpstest_command))
    application.add_handler(CommandHandler("dbtest", dbtest_command))
    application.add_handler(CommandHandler("founderstest", founderstest_command))
    return application
