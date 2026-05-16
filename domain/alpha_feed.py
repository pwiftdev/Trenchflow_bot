from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from typing import Optional

from domain.token_snapshot import TokenSnapshot


@dataclass(frozen=True)
class AlphaScanContext:
    group_title: Optional[str]
    group_id: int
    scanner_display: str
    scanned_at: datetime
    first_call_line: Optional[str]
    cross_group_count_30m: Optional[int] = None


def format_alpha_scan_alert(
    snapshot: TokenSnapshot,
    ctx: AlphaScanContext,
) -> str:
    group_name = escape(ctx.group_title or f"Group {ctx.group_id}")
    name = escape(snapshot.name or "Unknown")
    symbol = escape(snapshot.symbol or "?")
    mint = escape(snapshot.mint)
    scanner = escape(_limit(ctx.scanner_display, 80))
    time_utc = ctx.scanned_at.astimezone(timezone.utc).strftime("%H:%M UTC")

    lines = [
        f"🔔 <b>{group_name}</b> scanned a token",
        "",
        f"<b>{name} (${symbol})</b>",
        f"<code>{mint}</code>",
        "",
        f"├ MC @ scan: <b>{_fmt_usd(snapshot.market_cap)}</b>",
        f"├ Price: <b>{_fmt_price(snapshot.price_usd)}</b>",
        f"├ LP:  {_fmt_usd(snapshot.liquidity_usd)}",
        f"└ Vol: {_fmt_usd(snapshot.volume_h24)}",
    ]

    if ctx.cross_group_count_30m is not None and ctx.cross_group_count_30m > 1:
        n = ctx.cross_group_count_30m
        others = n - 1
        label = "group" if others == 1 else "groups"
        lines.append("")
        lines.append(f"🌐 <b>{n}</b> groups scanned this CA in the last 30m ({others} other {label})")

    if ctx.first_call_line:
        lines.extend(["", escape(ctx.first_call_line)])

    lines.extend(["", f"👤 {scanner} · 🕐 {time_utc}"])
    return "\n".join(lines)


def _limit(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _fmt_price(value: Optional[float]) -> str:
    if value is None:
        return "—"
    if value >= 1:
        return f"${value:.4f}".rstrip("0").rstrip(".")
    if value >= 0.0001:
        return f"${value:.6f}".rstrip("0").rstrip(".")
    return f"${value:.2e}"


def _fmt_usd(value: Optional[float]) -> str:
    if value is None:
        return "—"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.2f}K"
    if value >= 1:
        return f"${value:.2f}"
    if value >= 0.0001:
        return f"${value:.6f}".rstrip("0").rstrip(".")
    return f"${value:.2e}"
