from services.helius import _parse_mint_account, _parse_security


def test_parse_mint_account_authorities() -> None:
    sample = {
        "value": {
            "data": {
                "parsed": {
                    "type": "mint",
                    "info": {
                        "mintAuthority": None,
                        "freezeAuthority": None,
                        "supply": "1000000000",
                        "decimals": 6,
                    },
                }
            }
        }
    }
    parsed = _parse_mint_account(sample)
    assert parsed is not None
    assert parsed["mint_renounced"] is True
    assert parsed["freeze_renounced"] is True


def test_parse_security_top10_pct() -> None:
    mint = {
        "value": {
            "data": {
                "parsed": {
                    "type": "mint",
                    "info": {
                        "mintAuthority": None,
                        "freezeAuthority": None,
                        "supply": "1000",
                        "decimals": 0,
                    },
                }
            }
        }
    }
    largest = {
        "value": [
            {"address": "a", "uiAmount": 100.0},
            {"address": "b", "uiAmount": 50.0},
        ]
    }
    security = _parse_security(mint, largest)
    assert security.top10_holder_pct == 15.0
