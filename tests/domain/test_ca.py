from domain.ca import is_valid_solana_address


def test_valid_solana_mint() -> None:
    assert is_valid_solana_address("So11111111111111111111111111111111111111112")


def test_rejects_invalid_base58_chars() -> None:
    assert not is_valid_solana_address("0" * 32)
    assert not is_valid_solana_address("O" * 32)
    assert not is_valid_solana_address("I" * 32)
    assert not is_valid_solana_address("l" * 32)


def test_rejects_wrong_length() -> None:
    assert not is_valid_solana_address("short")
    assert not is_valid_solana_address("1" * 50)
