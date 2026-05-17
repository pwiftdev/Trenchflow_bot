"""Top-holder math with liquidity pool accounts excluded."""

from typing import Any, Optional


def lp_owner_addresses_from_pairs(pairs: list[dict[str, Any]]) -> frozenset[str]:
    """DexScreener pairAddress values are pool authorities — exclude from holder stats."""
    addresses: set[str] = set()
    for pair in pairs:
        pair_address = pair.get("pairAddress")
        if isinstance(pair_address, str) and pair_address.strip():
            addresses.add(pair_address.strip())
    return frozenset(addresses)


def top10_supply_percent_excluding_lp(
    holder_items: list[dict[str, Any]],
    *,
    total_supply: float,
    lp_owners: frozenset[str],
) -> Optional[float]:
    """Sum supply % of the 10 largest non-LP holders (items must be largest-first)."""
    if total_supply <= 0 or not holder_items:
        return None

    amounts: list[float] = []
    for item in holder_items:
        owner = item.get("owner")
        if isinstance(owner, str) and owner in lp_owners:
            continue

        amount = _to_float(item.get("ui_amount"))
        if amount is None or amount <= 0:
            continue

        amounts.append(amount)
        if len(amounts) >= 10:
            break

    if not amounts:
        return None

    return (sum(amounts) / total_supply) * 100.0


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
