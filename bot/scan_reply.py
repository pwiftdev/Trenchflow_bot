import structlog
from telegram import InlineKeyboardMarkup, Message
from telegram.error import BadRequest, TelegramError

from domain.scan_media import photo_url_candidates
from domain.telegram_caption import strip_html_tags
from domain.token_snapshot import TokenSnapshot

log = structlog.get_logger()


async def reply_scan_card(
    message: Message,
    *,
    caption: str,
    keyboard: InlineKeyboardMarkup,
    snapshot: TokenSnapshot,
) -> bool:
    for url in photo_url_candidates(snapshot):
        try:
            await message.reply_photo(
                photo=url,
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            return True
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

    if await _reply_text_html(message, caption=caption, keyboard=keyboard, snapshot=snapshot):
        return True

    return await _reply_plain_fallback(message, caption=caption, keyboard=keyboard, snapshot=snapshot)


async def edit_scan_card(
    message: Message,
    *,
    caption: str,
    keyboard: InlineKeyboardMarkup,
    snapshot: TokenSnapshot,
) -> bool:
    if message.photo:
        try:
            await message.edit_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            return True
        except BadRequest as exc:
            log.warning("scan_caption_edit_failed", ca=snapshot.mint, error=str(exc))

    if await _edit_text_html(message, caption=caption, keyboard=keyboard, snapshot=snapshot):
        return True

    return await _reply_plain_fallback(message, caption=caption, keyboard=keyboard, snapshot=snapshot)


async def _reply_text_html(
    message: Message,
    *,
    caption: str,
    keyboard: InlineKeyboardMarkup,
    snapshot: TokenSnapshot,
) -> bool:
    try:
        await message.reply_text(
            caption,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=keyboard,
        )
        return True
    except BadRequest as exc:
        log.warning("scan_text_html_rejected", ca=snapshot.mint, error=str(exc))
        return False
    except TelegramError as exc:
        log.warning("scan_text_failed", ca=snapshot.mint, error=str(exc))
        return False


async def _edit_text_html(
    message: Message,
    *,
    caption: str,
    keyboard: InlineKeyboardMarkup,
    snapshot: TokenSnapshot,
) -> bool:
    try:
        await message.edit_text(
            caption,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=keyboard,
        )
        return True
    except BadRequest as exc:
        log.warning("scan_text_edit_failed", ca=snapshot.mint, error=str(exc))
        return False
    except TelegramError as exc:
        log.warning("scan_text_edit_failed", ca=snapshot.mint, error=str(exc))
        return False


async def _reply_plain_fallback(
    message: Message,
    *,
    caption: str,
    keyboard: InlineKeyboardMarkup,
    snapshot: TokenSnapshot,
) -> bool:
    plain = strip_html_tags(caption)
    try:
        await message.reply_text(
            plain[:4096],
            disable_web_page_preview=True,
            reply_markup=keyboard,
        )
        return True
    except TelegramError as exc:
        log.error("scan_reply_failed", ca=snapshot.mint, error=str(exc))
        try:
            await message.reply_text(
                "Scan completed but Telegram could not display the card. Try /scan again.",
            )
        except TelegramError:
            pass
        return False
