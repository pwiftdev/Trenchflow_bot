from typing import Sequence

import structlog
from telegram import Bot, BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats
from telegram import BotCommandScopeChat, BotCommandScopeDefault
from telegram.error import ChatMigrated, TelegramError

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
        await _set_founders_commands(bot, settings.founders_chat_id)

    log.info(
        "bot_commands_registered",
        public=[c.command for c in PUBLIC_COMMANDS],
        founders_chat=settings.founders_chat_id is not None,
    )


async def _set_founders_commands(bot: Bot, chat_id: int) -> None:
    commands = list(PUBLIC_COMMANDS) + list(FOUNDERS_COMMANDS)
    scope = BotCommandScopeChat(chat_id=chat_id)
    try:
        await bot.set_my_commands(commands, scope=scope)
    except ChatMigrated as exc:
        new_chat_id = exc.migrate_to_chat_id
        log.warning(
            "founders_chat_migrated",
            old_chat_id=chat_id,
            new_chat_id=new_chat_id,
            hint="Update FOUNDERS_CHAT_ID in .env",
        )
        await bot.set_my_commands(
            commands,
            scope=BotCommandScopeChat(chat_id=new_chat_id),
        )
    except TelegramError as exc:
        log.warning(
            "founders_commands_skipped",
            chat_id=chat_id,
            error=str(exc),
        )
