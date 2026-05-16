from datetime import datetime
from typing import Optional

import structlog
from telegram import Update

from config.settings import get_settings
from db.queries import fetch_first_scan_in_chat, record_scan_event as db_record_scan_event
from db.session import create_engine, create_session_factory
from domain.call_pnl import caller_label, format_since_call_line
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

    display = caller_label(
        user_id=user.id,
        display_name=user.full_name or (f"@{user.username}" if user.username else ""),
    )

    settings = get_settings()
    if not settings.database_url:
        return format_since_call_line(
            first_market_cap_usd=None,
            current_market_cap_usd=snapshot.market_cap,
            first_scanned_at=datetime.now().astimezone(),
            first_caller_label=display,
            is_first_scan=True,
            current_caller_label=display,
        )

    engine = create_engine(settings)
    try:
        session_factory = create_session_factory(engine)
        async with session_factory() as session:
            first = await fetch_first_scan_in_chat(session, ca=mint, group_id=chat.id)
    except Exception as exc:
        log.warning("first_call_lookup_failed", error=str(exc), ca=mint, group_id=chat.id)
        return None
    finally:
        await engine.dispose()

    if first is None:
        return format_since_call_line(
            first_market_cap_usd=None,
            current_market_cap_usd=snapshot.market_cap,
            first_scanned_at=datetime.now().astimezone(),
            first_caller_label=display,
            is_first_scan=True,
            current_caller_label=display,
        )

    first_label = caller_label(user_id=first.user_id, display_name=f"User {first.user_id}")
    return format_since_call_line(
        first_market_cap_usd=first.market_cap_usd,
        current_market_cap_usd=snapshot.market_cap,
        first_scanned_at=first.scanned_at,
        first_caller_label=first_label,
        is_first_scan=False,
        current_caller_label=display,
    )


async def record_scan_event(
    update: Update,
    *,
    mint: str,
    scanned_at: datetime,
    snapshot: TokenSnapshot,
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
                    market_cap_usd=snapshot.market_cap,
                    price_usd=snapshot.price_usd,
                )
                await session.commit()
            except Exception as exc:
                await session.rollback()
                log.warning(
                    "scan_event_log_failed",
                    error=str(exc),
                    ca=mint,
                    group_id=chat.id,
                )
    finally:
        await engine.dispose()
