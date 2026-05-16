from domain.dex_orders import parse_dex_orders


def test_parse_dex_orders_profile_paid() -> None:
    info = parse_dex_orders(
        {
            "orders": [
                {"type": "tokenProfile", "status": "approved"},
                {"type": "tokenProfile", "status": "cancelled"},
            ],
            "boosts": [{"amount": 10}, {"amount": 30}],
        }
    )
    assert info.profile_paid is True
    assert info.boost_amount_total == 40
    assert info.boost_order_count == 2


def test_parse_dex_orders_empty() -> None:
    info = parse_dex_orders({"orders": [], "boosts": []})
    assert info.profile_paid is False
    assert info.boost_amount_total == 0
