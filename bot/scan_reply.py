import structlog
from telegram import InlineKeyboardMarkup, Message
from telegram.error import BadRequest, TelegramError

from domain.scan_media import photo_url_candidates
from domain.telegram_caption import (
    TELEGRAM_CAPTION_LIMIT,
    TELEGRAM_MESSAGE_LIMIT,
    fit_telegram_caption,
    strip_html_tags,
)
from domain.token_snapshot import TokenSnapshot

log = structlog.get_logger()


async def _try_reply_photo(
    message: Message,
    snapshot: TokenSnapshot,
    *,
    caption: str,
    keyboard: InlineKeyboardMarkup,
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
    return False


async def reply_scan_card(
    message: Message,
    *,
    caption: str,
    keyboard: InlineKeyboardMarkup,
    snapshot: TokenSnapshot,
) -> bool:
    photo_caption = fit_telegram_caption(caption, limit=TELEGRAM_CAPTION_LIMIT)
    if await _try_reply_photo(
        message,
        snapshot,
        caption=photo_caption,
        keyboard=keyboard,
    ):
        return True

    text_body = fit_telegram_caption(caption, limit=TELEGRAM_MESSAGE_LIMIT)
    if await _reply_text_html(
        message,
        caption=text_body,
        keyboard=keyboard,
        snapshot=snapshot,
    ):
        return True

    return await _reply_plain_fallback(
        message,
        caption=text_body,
        keyboard=keyboard,
        snapshot=snapshot,
    )


async def edit_scan_card(
    message: Message,
    *,
    caption: str,
    keyboard: InlineKeyboardMarkup,
    snapshot: TokenSnapshot,
) -> bool:
    photo_caption = fit_telegram_caption(caption, limit=TELEGRAM_CAPTION_LIMIT)

    if message.photo:
        try:
            await message.edit_caption(
                caption=photo_caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            return True
        except BadRequest as exc:
            log.warning("scan_caption_edit_failed", ca=snapshot.mint, error=str(exc))

    text_body = fit_telegram_caption(caption, limit=TELEGRAM_MESSAGE_LIMIT)
    if await _edit_text_html(
        message,
        caption=text_body,
        keyboard=keyboard,
        snapshot=snapshot,
    ):
        return True

    return await _reply_plain_fallback(
        message,
        caption=text_body,
        keyboard=keyboard,
        snapshot=snapshot,
    )


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
            plain[:TELEGRAM_MESSAGE_LIMIT],
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
