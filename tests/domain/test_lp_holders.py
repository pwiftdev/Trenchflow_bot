from domain.lp_holders import (
    lp_owner_addresses_from_pairs,
    top10_supply_percent_excluding_lp,
)

CHADIMALS_LP = "7QbZkgxxtAfihKF4iJ6oL2HhBhHRmtknzu1KVBScxZrB"
CHADIMALS_MINT = "tvEVEa9cLEo7BQrizEUHEibQhDwcZvoYJhStzNVpump"


def test_lp_owner_addresses_from_pairs_collects_pair_address() -> None:
    pairs = [
        {
            "pairAddress": CHADIMALS_LP,
            "baseToken": {"address": CHADIMALS_MINT},
        },
        {"pairAddress": "AnotherPool1111111111111111111111111111111"},
    ]
    assert lp_owner_addresses_from_pairs(pairs) == frozenset(
        {CHADIMALS_LP, "AnotherPool1111111111111111111111111111111"}
    )


def test_top10_excludes_lp_then_sums_next_ten_holders() -> None:
    total_supply = 1_000_000_000.0
    holders = [
        {"owner": CHADIMALS_LP, "ui_amount": 710_000_000},
        {"owner": "wallet2", "ui_amount": 50_000_000},
        {"owner": "wallet3", "ui_amount": 40_000_000},
        {"owner": "wallet4", "ui_amount": 30_000_000},
        {"owner": "wallet5", "ui_amount": 20_000_000},
        {"owner": "wallet6", "ui_amount": 10_000_000},
        {"owner": "wallet7", "ui_amount": 9_000_000},
        {"owner": "wallet8", "ui_amount": 8_000_000},
        {"owner": "wallet9", "ui_amount": 7_000_000},
        {"owner": "wallet10", "ui_amount": 6_000_000},
        {"owner": "wallet11", "ui_amount": 5_000_000},
    ]
    lp = frozenset({CHADIMALS_LP})

    pct = top10_supply_percent_excluding_lp(
        holders,
        total_supply=total_supply,
        lp_owners=lp,
    )

    # wallets 2–11: 50+40+...+5 = 185M → 18.5%
    assert pct == 18.5


def test_security_from_birdeye_accepts_top10_override() -> None:
    from domain.birdeye_parse import security_from_birdeye

    security = security_from_birdeye(
        {"top10HolderPercent": 0.71, "totalSupply": 1_000_000_000},
        top10_holder_pct=18.5,
    )
    assert security.top10_holder_pct == 18.5
