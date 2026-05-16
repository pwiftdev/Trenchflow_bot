from datetime import datetime, timezone
from typing import Optional


def format_since_call_line(
    *,
    first_market_cap_usd: Optional[float],
    current_market_cap_usd: Optional[float],
    first_scanned_at: datetime,
    first_caller_label: str,
    is_first_scan: bool,
    current_caller_label: str,
) -> str:
    if is_first_scan:
        mcap = _fmt_usd(current_market_cap_usd)
        return f"🔥 First call {current_caller_label} @ {mcap}"

    if first_market_cap_usd is None or current_market_cap_usd is None:
        ago = _format_ago(first_scanned_at)
        return f"🔥 First call {first_caller_label} · {ago}"

    pct = ((current_market_cap_usd - first_market_cap_usd) / first_market_cap_usd) * 100
    sign = "+" if pct > 0 else ""
    ago = _format_ago(first_scanned_at)
    return (
        f"📈 Since call @ {_fmt_usd(first_market_cap_usd)} → {_fmt_usd(current_market_cap_usd)} "
        f"({sign}{pct:.1f}%) · {first_caller_label} · {ago}"
    )


def caller_label(*, user_id: Optional[int], display_name: str) -> str:
    return display_name if display_name else (f"User {user_id}" if user_id else "Unknown")


def _format_ago(when: datetime) -> str:
    when_utc = when.astimezone(timezone.utc)
    seconds = int((datetime.now(timezone.utc) - when_utc).total_seconds())
    if seconds < 60:
        return f"{max(1, seconds)}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def _fmt_usd(value: Optional[float]) -> str:
    if value is None:
        return "—"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.2f}K"
    if value >= 1:
        return f"${value:.2f}"
    return f"${value:.6f}".rstrip("0").rstrip(".")
