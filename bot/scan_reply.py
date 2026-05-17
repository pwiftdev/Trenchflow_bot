import structlog
from telegram import InlineKeyboardMarkup, Message
from telegram.error import BadRequest, TelegramError

from domain.scan_card import photo_header_caption
from domain.scan_media import photo_url_candidates
from domain.telegram_caption import (
    TELEGRAM_CAPTION_LIMIT,
    TELEGRAM_MESSAGE_LIMIT,
    fit_telegram_caption,
    strip_html_tags,
)
from domain.token_snapshot import TokenSnapshot

log = structlog.get_logger()


def _fits_photo_caption(caption: str) -> bool:
    return len(caption) <= TELEGRAM_CAPTION_LIMIT


async def _try_reply_photo(
    message: Message,
    snapshot: TokenSnapshot,
    *,
    caption: str | None,
    keyboard: InlineKeyboardMarkup | None,
) -> bool:
    for url in photo_url_candidates(snapshot):
        try:
            await message.reply_photo(
                photo=url,
                caption=caption,
                parse_mode="HTML" if caption else None,
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
    if _fits_photo_caption(caption):
        if await _try_reply_photo(
            message,
            snapshot,
            caption=caption,
            keyboard=keyboard,
        ):
            return True
    else:
        await _try_reply_photo(
            message,
            snapshot,
            caption=photo_header_caption(snapshot),
            keyboard=None,
        )

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
    if message.photo and not _fits_photo_caption(caption):
        return await _replace_with_text_message(
            message,
            caption=fit_telegram_caption(caption, limit=TELEGRAM_MESSAGE_LIMIT),
            keyboard=keyboard,
            snapshot=snapshot,
        )

    if message.photo:
        try:
            await message.edit_caption(
                caption=fit_telegram_caption(caption, limit=TELEGRAM_CAPTION_LIMIT),
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


async def _replace_with_text_message(
    message: Message,
    *,
    caption: str,
    keyboard: InlineKeyboardMarkup,
    snapshot: TokenSnapshot,
) -> bool:
    """Photo messages cannot hold >1024 char captions — replace with a text message."""
    bot = message.get_bot()
    chat_id = message.chat_id
    thread_id = message.message_thread_id

    try:
        await message.delete()
    except TelegramError as exc:
        log.warning("scan_delete_for_text_replace_failed", ca=snapshot.mint, error=str(exc))

    await _try_reply_photo(
        message,
        snapshot,
        caption=photo_header_caption(snapshot),
        keyboard=None,
    )

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=caption,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=keyboard,
            message_thread_id=thread_id,
        )
        return True
    except BadRequest as exc:
        log.warning("scan_text_replace_rejected", ca=snapshot.mint, error=str(exc))
        return await _reply_plain_fallback(
            message,
            caption=caption,
            keyboard=keyboard,
            snapshot=snapshot,
        )
    except TelegramError as exc:
        log.warning("scan_text_replace_failed", ca=snapshot.mint, error=str(exc))
        return False


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
