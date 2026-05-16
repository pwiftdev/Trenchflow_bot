from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DexOrdersInfo:
    profile_paid: bool
    boost_amount_total: int
    boost_order_count: int


def parse_dex_orders(payload: Any) -> DexOrdersInfo:
    if not isinstance(payload, dict):
        return DexOrdersInfo(profile_paid=False, boost_amount_total=0, boost_order_count=0)

    orders = payload.get("orders")
    boosts = payload.get("boosts")

    profile_paid = False
    if isinstance(orders, list):
        profile_paid = any(
            isinstance(order, dict)
            and order.get("type") == "tokenProfile"
            and order.get("status") == "approved"
            for order in orders
        )

    boost_amount_total = 0
    boost_order_count = 0
    if isinstance(boosts, list):
        for boost in boosts:
            if not isinstance(boost, dict):
                continue
            boost_order_count += 1
            try:
                boost_amount_total += int(boost.get("amount") or 0)
            except (TypeError, ValueError):
                continue

    return DexOrdersInfo(
        profile_paid=profile_paid,
        boost_amount_total=boost_amount_total,
        boost_order_count=boost_order_count,
    )
