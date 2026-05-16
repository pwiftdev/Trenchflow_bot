from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from typing import Optional

from domain.security_snapshot import SecuritySnapshot
from domain.token_snapshot import TokenSnapshot


@dataclass(frozen=True)
class ScanMeta:
    scanner_display: str
    scanned_at: datetime
    chat_title: Optional[str]
    first_call_line: Optional[str] = None


def format_scan_card(
    snapshot: TokenSnapshot,
    meta: ScanMeta,
    security: Optional[SecuritySnapshot] = None,
) -> str:
    name = escape(snapshot.name or "Unknown")
    symbol = escape(snapshot.symbol or "?")
    mint = escape(snapshot.mint)

    lines = [
        f"<b>{name} (${symbol})</b>",
        f"<code>{mint}</code>",
        "",
        _format_subline(snapshot, security),
        "",
        "📊 <b>Stats</b>",
        f"├ USD: <b>{_fmt_price(snapshot.price_usd)}</b> ({_fmt_pct(snapshot.price_change_h24)})",
        f"├ MC:  <b>{_fmt_usd(snapshot.market_cap)}</b>",
        f"├ Vol: {_fmt_usd(snapshot.volume_h24)}",
        f"├ LP:  {_fmt_usd(snapshot.liquidity_usd)}",
    ]

    supply_line = _format_supply(snapshot, security)
    if supply_line:
        lines.append(f"├ Sup: {supply_line}")

    lines.append(
        f"├ 1H:  {_fmt_pct(snapshot.price_change_h1)} "
        f"🟢{_fmt_count(snapshot.txns_h1_buys)} 🔴{_fmt_count(snapshot.txns_h1_sells)}"
    )
    lines.append(f"└ ATH: {_format_ath(snapshot)}")

    social_block = _format_socials(snapshot)
    if social_block:
        lines.extend(["", social_block])

    security_block = _format_security(snapshot, security)
    if security_block:
        lines.extend(["", security_block])

    if meta.first_call_line:
        lines.extend(["", escape(meta.first_call_line)])

    lines.extend(
        [
            "",
            f"👤 {_escape_limited(meta.scanner_display, 64)} · "
            f"🕐 {meta.scanned_at.astimezone(timezone.utc).strftime('%H:%M UTC')}",
        ]
    )

    return "\n".join(lines)


def _format_subline(snapshot: TokenSnapshot, security: Optional[SecuritySnapshot]) -> str:
    launch = _format_launchpad(snapshot.dex_id, snapshot.labels)
    age = _format_age(snapshot.pair_created_at_ms)
    holders = _fmt_count(security.holder_count if security else None)
    return f"🌱 {launch} · #SOL · {age} · 👥{holders}"


def _format_launchpad(dex_id: Optional[str], labels: list[str]) -> str:
    if dex_id:
        return escape(dex_id)
    if labels:
        return escape(labels[0])
    return "—"


def _format_socials(snapshot: TokenSnapshot) -> Optional[str]:
    if not snapshot.socials and not snapshot.websites:
        return None

    parts: list[str] = []
    for label, url in snapshot.socials[:4]:
        short = label.lower()
        if "twitter" in short or short == "x":
            parts.append(f'<a href="{escape(url)}">X</a>')
        else:
            parts.append(f'<a href="{escape(url)}">{escape(label)}</a>')
    for label, url in snapshot.websites[:2]:
        parts.append(f'<a href="{escape(url)}">{escape(label)}</a>')

    if not parts:
        return None

    return "🔗 <b>Socials</b>\n└ " + " · ".join(parts)


def _format_security(
    snapshot: TokenSnapshot,
    security: Optional[SecuritySnapshot],
) -> str:
    lines = ["🔒 <b>Security</b>"]

    if security is None:
        lines.append("├ Fresh: — <i>(needs Helius)</i>")
        lines.append("├ Top 10: —")
        lines.append("├ Mint: —")
        lines.append("├ Freeze: —")
    else:
        if security.fresh_1d_pct is not None or security.fresh_7d_pct is not None:
            f1 = _fmt_pct(security.fresh_1d_pct) if security.fresh_1d_pct is not None else "—"
            f7 = _fmt_pct(security.fresh_7d_pct) if security.fresh_7d_pct is not None else "—"
            lines.append(f"├ Fresh: {f1} 1D | {f7} 7D")
        else:
            lines.append("├ Fresh: — <i>(holder-age — soon)</i>")

        top10 = _fmt_pct(security.top10_holder_pct) if security.top10_holder_pct is not None else "—"
        holders = _fmt_count(security.holder_count)
        lines.append(f"├ Top 10: {top10} | {holders} total")

        lines.append(f"├ Mint: {_authority_label(security.mint_renounced, good_when_true=True)}")
        lines.append(f"├ Freeze: {_authority_label(security.freeze_renounced, good_when_true=True)}")

        dev = security.dev_sold_label or "— <i>(soon)</i>"
        lines.append(f"├ Dev: {escape(dev)}")

    lines.append(f"└ DEX Paid: {_format_dex_paid(snapshot)}")

    return "\n".join(lines)


def _format_dex_paid(snapshot: TokenSnapshot) -> str:
    profile_paid = snapshot.dex_profile_paid
    boost_total = snapshot.dex_boost_amount_total

    if profile_paid and boost_total:
        return f"🟢 profile · {boost_total} boost"
    if profile_paid:
        return "🟢 profile"
    if boost_total:
        return f"🔵 {boost_total} boost"
    if (snapshot.boosts_active or 0) > 0:
        return "🔵 active boost"
    return "—"


def _authority_label(renounced: Optional[bool], *, good_when_true: bool) -> str:
    if renounced is None:
        return "—"
    if renounced:
        return "🟢 renounced" if good_when_true else "🔴 renounced"
    return "🔴 active"


def _format_supply(snapshot: TokenSnapshot, security: Optional[SecuritySnapshot]) -> Optional[str]:
    if security and security.supply_ui:
        total = escape(security.supply_ui)
        return f"{total}/{total}"
    return None


def _format_ath(snapshot: TokenSnapshot) -> str:
    # DexScreener does not provide ATH; reserved for a future price-history source.
    return "— <i>(price history soon)</i>"


def _format_age(pair_created_at_ms: Optional[int]) -> str:
    if pair_created_at_ms is None:
        return "—"
    created = datetime.fromtimestamp(pair_created_at_ms / 1000, tz=timezone.utc)
    delta = datetime.now(timezone.utc) - created
    seconds = int(delta.total_seconds())
    if seconds < 3600:
        return f"{max(1, seconds // 60)}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


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
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.2f}K"
    if value >= 1:
        return f"${value:.2f}"
    if value >= 0.0001:
        return f"${value:.6f}".rstrip("0").rstrip(".")
    return f"${value:.2e}"


def _fmt_pct(value: Optional[float]) -> str:
    if value is None:
        return "—"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.0f}%" if abs(value) >= 10 else f"{sign}{value:.1f}%"


def _fmt_count(value: Optional[int]) -> str:
    if value is None:
        return "—"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def _escape_limited(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return escape(text)
    return escape(text[: max_len - 1]) + "…"
