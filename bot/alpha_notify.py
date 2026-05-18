from datetime import datetime, timedelta
from typing import Optional

import structlog
from telegram import Bot
from telegram import Update
from telegram.error import ChatMigrated

from bot.scan_keyboard import build_scan_keyboard
from config.settings import Settings, get_settings
from db import runtime as db_runtime
from db.queries import count_distinct_groups_for_ca
from domain.alpha_feed import AlphaScanContext, format_alpha_scan_alert
from domain.scan_card import ScanMeta
from domain.token_snapshot import TokenSnapshot

log = structlog.get_logger()


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
    if not db_runtime.database_enabled(settings):
        return None

    window_minutes = settings.alpha_cross_group_window_minutes
    since = scanned_at - timedelta(minutes=window_minutes)
    try:
        async with db_runtime.session_factory()() as session:
            return await count_distinct_groups_for_ca(session, ca=mint, since=since)
    except Exception as exc:
        log.warning("alpha_cross_group_count_failed", ca=mint, error=str(exc))
        return None


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
    keyboard = build_scan_keyboard(snapshot)

    founders_chat_id = settings.founders_chat_id
    assert founders_chat_id is not None

    try:
        await bot.send_message(
            chat_id=founders_chat_id,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=keyboard,
        )
    except ChatMigrated as exc:
        log.warning(
            "founders_chat_migrated",
            old_chat_id=founders_chat_id,
            new_chat_id=exc.new_chat_id,
            hint="Update FOUNDERS_CHAT_ID in .env",
        )
        try:
            await bot.send_message(
                chat_id=exc.new_chat_id,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=keyboard,
            )
        except Exception as retry_exc:
            log.warning(
                "alpha_feed_send_failed",
                founders_chat_id=exc.new_chat_id,
                ca=snapshot.mint,
                group_id=chat.id,
                error=str(retry_exc),
            )
    except Exception as exc:
        log.warning(
            "alpha_feed_send_failed",
            founders_chat_id=founders_chat_id,
            ca=snapshot.mint,
            group_id=chat.id,
            error=str(exc),
        )
