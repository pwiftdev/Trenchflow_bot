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
    caller = _compact_caller(first_caller_label if not is_first_scan else current_caller_label)

    if is_first_scan:
        mcap = _fmt_usd(current_market_cap_usd)
        return f"🔥 {caller} @ {mcap}"

    if first_market_cap_usd is None or current_market_cap_usd is None:
        return f"🔥 {caller} · {_format_ago(first_scanned_at)}"

    pct = ((current_market_cap_usd - first_market_cap_usd) / first_market_cap_usd) * 100
    sign = "+" if pct > 0 else ""
    return (
        f"📈 {_fmt_usd(first_market_cap_usd)}→{_fmt_usd(current_market_cap_usd)} "
        f"{sign}{pct:.0f}% · {caller} · {_format_ago(first_scanned_at)}"
    )


def _compact_caller(label: str) -> str:
    if "(@" in label:
        start = label.index("(@")
        return label[start + 1 :].rstrip(")")
    if label.startswith("@"):
        return label
    return label.split(" · ")[0].split()[0][:20]


def caller_label(
    *,
    user_id: Optional[int],
    full_name: Optional[str] = None,
    username: Optional[str] = None,
) -> str:
    if full_name and username:
        return f"{full_name} (@{username})"
    if username:
        return f"@{username}"
    if full_name:
        return full_name
    if user_id is not None:
        return f"User {user_id}"
    return "Unknown"


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
