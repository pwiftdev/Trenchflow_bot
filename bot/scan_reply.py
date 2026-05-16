import structlog
from telegram import InlineKeyboardMarkup, Message
from telegram.error import BadRequest, TelegramError

from domain.scan_media import photo_url_candidates
from domain.token_snapshot import TokenSnapshot

log = structlog.get_logger()


async def reply_scan_card(
    message: Message,
    *,
    caption: str,
    keyboard: InlineKeyboardMarkup,
    snapshot: TokenSnapshot,
) -> None:
    for url in photo_url_candidates(snapshot):
        try:
            await message.reply_photo(
                photo=url,
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            return
        except BadRequest as exc:
            log.warning(
                "scan_photo_rejected",
                ca=snapshot.mint,
                url=url,
                error=str(exc),
            )
        except TelegramError as exc:
            log.warning(
                "scan_photo_failed",
                ca=snapshot.mint,
                url=url,
                error=str(exc),
            )

    await message.reply_text(
        caption,
        parse_mode="HTML",
        disable_web_page_preview=False,
        reply_markup=keyboard,
    )
