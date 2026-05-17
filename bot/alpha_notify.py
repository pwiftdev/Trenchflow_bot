from datetime import datetime, timedelta
from typing import Optional

import structlog
from telegram import Bot
from telegram import Update

from bot.scan_keyboard import build_scan_keyboard
from config.settings import Settings, get_settings
from db.queries import count_distinct_groups_for_ca
from db.session import create_engine, create_session_factory
from domain.alpha_feed import AlphaScanContext, format_alpha_scan_alert
from domain.scan_card import ScanMeta
from domain.token_snapshot import TokenSnapshot

log = structlog.get_logger()

_CROSS_GROUP_WINDOW_MINUTES = 30


def _should_notify(update: Update, settings: Settings) -> bool:
    if settings.founders_chat_id is None:
        return False
    chat = update.effective_chat
    if chat is None:
        return False
    if chat.id == settings.founders_chat_id:
        return False
    if chat.type == "private":
        return False
    return chat.type in ("group", "supergroup", "channel")


async def _fetch_cross_group_count(mint: str, scanned_at: datetime) -> Optional[int]:
    settings = get_settings()
    if not settings.database_url:
        return None

    since = scanned_at - timedelta(minutes=_CROSS_GROUP_WINDOW_MINUTES)
    engine = create_engine(settings)
    try:
        session_factory = create_session_factory(engine)
        async with session_factory() as session:
            return await count_distinct_groups_for_ca(session, ca=mint, since=since)
    except Exception as exc:
        log.warning("alpha_cross_group_count_failed", ca=mint, error=str(exc))
        return None
    finally:
        await engine.dispose()


async def notify_founders_scan(
    bot: Bot,
    *,
    update: Update,
    snapshot: TokenSnapshot,
    meta: ScanMeta,
    scanned_at: datetime,
) -> None:
    settings = get_settings()
    if not _should_notify(update, settings):
        return

    chat = update.effective_chat
    assert chat is not None

    cross_group_count = await _fetch_cross_group_count(snapshot.mint, scanned_at)

    ctx = AlphaScanContext(
        group_title=meta.chat_title or chat.title,
        group_id=chat.id,
        scanner_display=meta.scanner_display,
        scanned_at=scanned_at,
        first_call_line=meta.first_call_line,
        cross_group_count_30m=cross_group_count,
    )
    text = format_alpha_scan_alert(snapshot, ctx)
    keyboard = build_scan_keyboard(snapshot.mint)

    try:
        await bot.send_message(
            chat_id=settings.founders_chat_id,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=keyboard,
        )
    except Exception as exc:
        log.warning(
            "alpha_feed_send_failed",
            founders_chat_id=settings.founders_chat_id,
            ca=snapshot.mint,
            group_id=chat.id,
            error=str(exc),
        )
