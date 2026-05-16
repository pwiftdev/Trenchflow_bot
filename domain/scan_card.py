from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from typing import Optional

from domain.token_snapshot import TokenSnapshot


@dataclass(frozen=True)
class ScanMeta:
    scanner_display: str
    scanned_at: datetime
    chat_title: Optional[str]


def format_scan_card(snapshot: TokenSnapshot, meta: ScanMeta) -> str:
    symbol = escape(snapshot.symbol or "?")
    name = escape(snapshot.name or "Unknown")
    mint = escape(snapshot.mint)
    dex = escape(snapshot.dex_id or "—")
    scanner = escape(meta.scanner_display)
    scanned_at = meta.scanned_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    where = escape(meta.chat_title) if meta.chat_title else "DM"

    lines = [
        f"<b>${symbol}</b> · {name}",
        f"<code>{mint}</code>",
        "",
        f"💵 Price: <b>{_fmt_usd(snapshot.price_usd)}</b>",
        f"📊 MCap at scan: <b>{_fmt_usd(snapshot.market_cap)}</b>",
        f"💧 Liquidity: {_fmt_usd(snapshot.liquidity_usd)}",
        f"📈 24h: {_fmt_pct(snapshot.price_change_h24)} · Vol {_fmt_usd(snapshot.volume_h24)}",
    ]

    if snapshot.fdv is not None and snapshot.market_cap != snapshot.fdv:
        lines.append(f"🔢 FDV: {_fmt_usd(snapshot.fdv)}")

    lines.extend(
        [
            "",
            f"🕐 Scanned: {scanned_at}",
            f"👤 By: {scanner}",
            f"💬 In: {where}",
        ]
    )

    link_lines = []
    if snapshot.pair_url:
        link_lines.append(f'<a href="{escape(snapshot.pair_url)}">DexScreener</a>')
    for label, url in snapshot.websites[:3]:
        link_lines.append(f'<a href="{escape(url)}">{escape(label)}</a>')
    for label, url in snapshot.socials[:3]:
        link_lines.append(f'<a href="{escape(url)}">{escape(label)}</a>')

    if link_lines:
        lines.extend(["", "🔗 " + " · ".join(link_lines)])

    lines.append("")
    lines.append(f"DEX: {dex}")

    return "\n".join(lines)


def _fmt_usd(value: Optional[float]) -> str:
    if value is None:
        return "—"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.2f}K"
    if value >= 1:
        return f"${value:.4f}".rstrip("0").rstrip(".")
    if value >= 0.0001:
        return f"${value:.6f}".rstrip("0").rstrip(".")
    return f"${value:.2e}"


def _fmt_pct(value: Optional[float]) -> str:
    if value is None:
        return "—"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"
