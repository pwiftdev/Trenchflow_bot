from datetime import datetime
from typing import Optional

import structlog
from telegram import Update

from config.settings import get_settings
from db.queries import fetch_first_scan_in_chat, record_scan_event as db_record_scan_event
from db.session import create_engine, create_session_factory
from domain.scan_card import ScanMeta
from domain.token_snapshot import TokenSnapshot

log = structlog.get_logger()


def build_scan_meta(
    update: Update,
    *,
    scanned_at: datetime,
    snapshot: TokenSnapshot,
    first_call_line: Optional[str],
) -> ScanMeta:
    user = update.effective_user
    chat = update.effective_chat

    if user is None:
        scanner_display = "Unknown"
    elif user.username:
        scanner_display = f"{user.full_name} (@{user.username})"
    else:
        scanner_display = user.full_name or f"User {user.id}"

    chat_title: Optional[str] = None
    if chat and chat.type in ("group", "supergroup", "channel"):
        chat_title = chat.title

    return ScanMeta(
        scanner_display=scanner_display,
        scanned_at=scanned_at,
        chat_title=chat_title,
        first_call_line=first_call_line,
    )


async def build_first_call_line(
    update: Update,
    *,
    mint: str,
    snapshot: TokenSnapshot,
) -> Optional[str]:
    chat = update.effective_chat
    user = update.effective_user
    if chat is None or user is None:
        return None

    settings = get_settings()
    if not settings.database_url:
        mcap = _fmt_usd(snapshot.market_cap)
        return f"🔥 First call {user.full_name} @ {mcap}"

    engine = create_engine(settings)
    try:
        session_factory = create_session_factory(engine)
        async with session_factory() as session:
            first = await fetch_first_scan_in_chat(session, ca=mint, group_id=chat.id)
    except Exception as exc:
        log.warning("first_call_lookup_failed", error=str(exc))
        return None
    finally:
        await engine.dispose()

    mcap = _fmt_usd(snapshot.market_cap)
    if first is None:
        return f"🔥 First call {user.full_name} @ {mcap}"

    if first.user_id == user.id:
        return f"🔥 First call you @ {mcap}"

    return (
        f"🔥 First call User {first.user_id} · "
        f"{first.scanned_at.strftime('%Y-%m-%d %H:%M UTC')}"
    )


async def record_scan_event(
    update: Update,
    *,
    mint: str,
    scanned_at: datetime,
) -> None:
    settings = get_settings()
    if not settings.database_url:
        return

    chat = update.effective_chat
    user = update.effective_user
    if chat is None:
        return

    engine = create_engine(settings)
    try:
        session_factory = create_session_factory(engine)
        async with session_factory() as session:
            try:
                await db_record_scan_event(
                    session,
                    ca=mint,
                    group_id=chat.id,
                    group_name=chat.title,
                    user_id=user.id if user else None,
                    scanned_at=scanned_at,
                )
                await session.commit()
            except Exception as exc:
                await session.rollback()
                log.warning("scan_event_log_failed", error=str(exc), ca=mint)
    finally:
        await engine.dispose()


def _fmt_usd(value: Optional[float]) -> str:
    if value is None:
        return "—"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.2f}K"
    return f"${value:.2f}"
