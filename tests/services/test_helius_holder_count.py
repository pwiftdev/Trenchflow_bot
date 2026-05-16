from services.helius import _parse_holder_count


def test_parse_holder_count_from_total() -> None:
    assert _parse_holder_count({"total": 1420, "token_accounts": []}) == 1420


def test_parse_holder_count_missing() -> None:
    assert _parse_holder_count({}) is None
