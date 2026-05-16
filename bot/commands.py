from typing import Sequence

import structlog
from telegram import Bot, BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats
from telegram import BotCommandScopeChat, BotCommandScopeDefault

from config.settings import Settings

log = structlog.get_logger()

PUBLIC_COMMANDS: tuple[BotCommand, ...] = (
    BotCommand("scan", "Token card — price, MC, LP, security, call tracking"),
    BotCommand("help", "List commands and how to use Trenchflow"),
)

FOUNDERS_COMMANDS: tuple[BotCommand, ...] = (
    BotCommand("founderstest", "Verify bot can post in this chat"),
)


async def register_bot_commands(bot: Bot, settings: Settings) -> None:
    scopes: Sequence = (
        BotCommandScopeDefault(),
        BotCommandScopeAllPrivateChats(),
        BotCommandScopeAllGroupChats(),
    )
    for scope in scopes:
        await bot.set_my_commands(list(PUBLIC_COMMANDS), scope=scope)

    if settings.founders_chat_id is not None:
        founders_scope = BotCommandScopeChat(chat_id=settings.founders_chat_id)
        await bot.set_my_commands(
            list(PUBLIC_COMMANDS) + list(FOUNDERS_COMMANDS),
            scope=founders_scope,
        )

    log.info(
        "bot_commands_registered",
        public=[c.command for c in PUBLIC_COMMANDS],
        founders_chat=settings.founders_chat_id is not None,
    )
