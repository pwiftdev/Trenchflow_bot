from typing import Optional

from telegram import Message
from telegram.constants import MessageEntityType
from telegram.ext import filters

from domain.ca import extract_solana_mint_from_text


def message_text(message: Message) -> Optional[str]:
    raw = message.text or message.caption
    if not raw:
        return None
    return raw.strip().strip("\ufeff")


def message_has_bot_command(message: Message) -> bool:
    if not message.entities:
        return False
    return any(entity.type == MessageEntityType.BOT_COMMAND for entity in message.entities)


class _SolanaMintMessage(filters.MessageFilter):
    def filter(self, message: Message) -> bool:
        if message_has_bot_command(message):
            return False
        text = message_text(message)
        if not text:
            return False
        return extract_solana_mint_from_text(text) is not None


HAS_SOLANA_MINT = _SolanaMintMessage()
