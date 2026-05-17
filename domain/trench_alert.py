"""Holder tag breakdown from Birdeye token holder profile."""

from dataclasses import dataclass
from typing import Any, Optional

TAG_ORDER = ("bundler", "sniper", "insider", "dev", "smart_trader")

TAG_LABELS = {
    "bundler": "Bundlers",
    "sniper": "Snipers",
    "insider": "Insiders",
    "dev": "Dev",
    "smart_trader": "Smart",
}


@dataclass(frozen=True)
class HolderTagRow:
    tag: str
    label: str
    holder_count: int
    percent_of_supply: Optional[float]


@dataclass(frozen=True)
class TrenchAlert:
    total_holders: Optional[int]
    labeled_supply_pct: Optional[float]
    tags: tuple[HolderTagRow, ...]


def holder_profile_from_birdeye(data: dict[str, Any]) -> TrenchAlert:
    summary = data.get("holder_summary") or {}
    tags_raw = data.get("tags") or []
    by_tag: dict[str, dict[str, Any]] = {}
    for row in tags_raw:
        if isinstance(row, dict) and row.get("tag"):
            by_tag[str(row["tag"])] = row

    tags: list[HolderTagRow] = []
    for tag in TAG_ORDER:
        row = by_tag.get(tag, {})
        tags.append(
            HolderTagRow(
                tag=tag,
                label=TAG_LABELS.get(tag, tag),
                holder_count=_to_int(row.get("holder_count")) or 0,
                percent_of_supply=_to_float(row.get("percent_of_supply")),
            )
        )

    return TrenchAlert(
        total_holders=_to_int(summary.get("total_holder")),
        labeled_supply_pct=_to_float(summary.get("percent_of_supply")),
        tags=tuple(tags),
    )


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
