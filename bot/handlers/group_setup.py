import structlog
from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import ContextTypes

log = structlog.get_logger()

_GROUP_WELCOME = """<b>Trenchflow</b> added — paste a contract address for an instant scan.

<b>Group tip:</b> if paste does nothing but <code>/scan</code> works, open @BotFather → /setprivacy → <b>Disable</b>, remove me from this group, then add me again. Telegram blocks plain messages to bots until privacy is off."""


async def on_bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.my_chat_member is None:
        return

    chat = update.effective_chat
    if chat is None or chat.type not in ("group", "supergroup"):
        return

    new = update.my_chat_member.new_chat_member
    old = update.my_chat_member.old_chat_member
    if new.user.id != context.bot.id:
        return

    if new.status not in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR):
        return

    if old.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR):
        return

    try:
        await chat.send_message(_GROUP_WELCOME, parse_mode="HTML")
    except Exception as exc:
        log.warning("group_welcome_failed", chat_id=chat.id, error=str(exc))
