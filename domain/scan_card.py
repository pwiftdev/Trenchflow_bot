from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from typing import Optional

from domain.telegram_caption import href_attr
from domain.security_snapshot import SecuritySnapshot
from domain.token_snapshot import TokenSnapshot
from domain.trench_alert import TrenchAlert

_BRANCH = " ├"
_LAST = " └"
_TRENCH_DISPLAY_TAGS = ("bundler", "sniper", "insider", "smart_trader")


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
    trench_alert: Optional[TrenchAlert] = None,
) -> str:
    name = escape(snapshot.name or "Unknown")
    symbol = escape(snapshot.symbol or "?")
    mint = escape(snapshot.mint)
    header_emoji = _header_emoji(snapshot)

    blocks: list[str] = [
        f"{header_emoji} <b>{name} (${symbol})</b>",
        f"{_BRANCH} <code>{mint}</code>",
        _format_subline(snapshot, security),
        "",
        _format_stats(snapshot, security),
    ]

    social_block = _format_socials(snapshot)
    if social_block:
        blocks.extend(["", social_block])

    security_block = _format_security(snapshot, security)
    if security_block:
        blocks.extend(["", security_block])

    trench_block = _format_trench_alert(trench_alert)
    if trench_block:
        blocks.extend(["", trench_block])

    if meta.first_call_line:
        blocks.extend(["", escape(meta.first_call_line)])

    return "\n".join(blocks)


def _header_emoji(snapshot: TokenSnapshot) -> str:
    dex = (snapshot.dex_id or "").lower()
    if dex == "pumpfun" or "pump" in snapshot.labels:
        return "💊"
    return "🪙"


def _format_subline(snapshot: TokenSnapshot, security: Optional[SecuritySnapshot]) -> str:
    age = _format_age(snapshot.pair_created_at_ms)
    holders = _fmt_count(security.holder_count if security else None)
    return f"{_LAST} #SOL|🌱{age}|👁️{holders}"


def _format_stats(snapshot: TokenSnapshot, security: Optional[SecuritySnapshot]) -> str:
    lines = [
        "📊 Stats",
        f"{_BRANCH} MC {_fmt_usd(snapshot.market_cap)}",
        f"{_BRANCH} Vol {_fmt_usd(snapshot.volume_h24)}",
        f"{_BRANCH} LP {_fmt_usd(snapshot.liquidity_usd)}",
    ]

    supply_line = _format_supply(snapshot, security)
    if supply_line:
        lines.append(f"{_BRANCH} Sup {supply_line}")

    lines.append(
        f"{_BRANCH} 1H {_fmt_pct(snapshot.price_change_h1)} "
        f"🟩{_fmt_count(snapshot.txns_h1_buys)} 🟥{_fmt_count(snapshot.txns_h1_sells)}"
    )
    lines.append(f"{_LAST} ATH {_format_ath(snapshot)}")
    return "\n".join(lines)


def _format_socials(snapshot: TokenSnapshot) -> Optional[str]:
    links = _token_social_links(snapshot)
    if not links:
        return None
    return "🔗 Socials\n" + f"{_LAST} " + " · ".join(links)


def _token_social_links(snapshot: TokenSnapshot) -> list[str]:
    links: list[str] = []
    for label, url in snapshot.socials[:4]:
        short = label.lower()
        if "twitter" in short or short == "x":
            links.append(f'<a href="{href_attr(url)}">Twitter</a>')
        else:
            links.append(f'<a href="{href_attr(url)}">{escape(label)}</a>')
    for label, url in snapshot.websites[:2]:
        links.append(f'<a href="{href_attr(url)}">{escape(label)}</a>')
    return links


def _format_trench_alert(alert: Optional[TrenchAlert]) -> Optional[str]:
    if alert is None or not alert.tags:
        return None

    by_tag = {row.tag: row for row in alert.tags}
    rows: list[str] = []
    for tag in _TRENCH_DISPLAY_TAGS:
        row = by_tag.get(tag)
        if row is None:
            continue
        rows.append(f"{escape(row.label)} {_fmt_trench_supply_pct(row.percent_of_supply)}")

    if not rows:
        return None

    lines = ["⚠️ Trench"]
    for index, content in enumerate(rows):
        branch = _LAST if index == len(rows) - 1 else _BRANCH
        lines.append(f"{branch} {content}")
    return "\n".join(lines)


def _format_security(
    snapshot: TokenSnapshot,
    security: Optional[SecuritySnapshot],
) -> str:
    rows: list[str] = []

    if security is None:
        rows.extend(["T10 —", "Holders —", "DS —", f"DP {_format_dex_paid(snapshot)}"])
    else:
        if security.fresh_1d_pct is not None or security.fresh_7d_pct is not None:
            f1 = _fmt_pct(security.fresh_1d_pct) if security.fresh_1d_pct is not None else "—"
            f7 = _fmt_pct(security.fresh_7d_pct) if security.fresh_7d_pct is not None else "—"
            rows.append(f"Fresh {f1} 1D | {f7} 7D")

        top10 = _fmt_pct(security.top10_holder_pct) if security.top10_holder_pct is not None else "—"
        rows.append(f"T10 {top10}")
        rows.append(f"Holders {_fmt_count(security.holder_count)}")
        rows.append(f"DS {_format_dev_sold(security)}")
        rows.append(f"DP {_format_dex_paid(snapshot)}")

    lines = ["🔒 Security"]
    for index, content in enumerate(rows):
        branch = _LAST if index == len(rows) - 1 else _BRANCH
        lines.append(f"{branch} {content}")
    return "\n".join(lines)


def _format_dev_sold(security: SecuritySnapshot) -> str:
    label = security.dev_sold_label
    if label == "🟢":
        return "🟢"
    if label and label.startswith("🔴"):
        return label
    return "—"


def _format_dex_paid(snapshot: TokenSnapshot) -> str:
    if snapshot.dex_profile_paid:
        return "🟢"
    return "🔴"


def _authority_emoji(renounced: Optional[bool]) -> str:
    if renounced is None:
        return "—"
    return "🟢" if renounced else "🔴"


def _format_supply(snapshot: TokenSnapshot, security: Optional[SecuritySnapshot]) -> Optional[str]:
    if security and security.supply_ui:
        return escape(security.supply_ui)
    return None


def _format_ath(snapshot: TokenSnapshot) -> str:
    if snapshot.ath_price_usd is None:
        return "—"
    if snapshot.price_usd and snapshot.market_cap and snapshot.price_usd > 0:
        ath_mcap = snapshot.ath_price_usd * (snapshot.market_cap / snapshot.price_usd)
        drawdown = ((snapshot.price_usd / snapshot.ath_price_usd) - 1) * 100
        return f"{_fmt_usd(ath_mcap)} ({_fmt_pct(drawdown)})"
    return _fmt_price(snapshot.ath_price_usd)


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
        return f"${value / 1_000:.1f}K"
    if value >= 1:
        return f"${value:.2f}"
    if value >= 0.0001:
        return f"${value:.6f}".rstrip("0").rstrip(".")
    return f"${value:.2e}"


def _fmt_trench_supply_pct(value: Optional[float]) -> str:
    if value is None or value == 0:
        return "0%"
    return _fmt_pct(value)


def _fmt_pct(value: Optional[float]) -> str:
    if value is None:
        return "—"
    sign = "+" if value > 0 else ""
    if abs(value) >= 10:
        return f"{sign}{value:.0f}%"
    return f"{sign}{value:.1f}%"


def _fmt_count(value: Optional[int]) -> str:
    if value is None:
        return "—"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)
