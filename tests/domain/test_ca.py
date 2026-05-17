from domain.ca import extract_solana_mint_from_text, is_valid_solana_address

CHADIMALS_MINT = "tvEVEa9cLEo7BQrizEUHEibQhDwcZvoYJhStzNVpump"


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


def test_extract_mint_from_plain_text() -> None:
    assert extract_solana_mint_from_text(CHADIMALS_MINT) == CHADIMALS_MINT


def test_extract_mint_from_dexscreener_url() -> None:
    text = f"https://dexscreener.com/solana/{CHADIMALS_MINT}"
    assert extract_solana_mint_from_text(text) == CHADIMALS_MINT


def test_extract_mint_ignores_invalid_base58_in_text() -> None:
    assert extract_solana_mint_from_text("0" * 44) is None
    assert extract_solana_mint_from_text("no address here") is None


def test_extract_returns_first_valid_mint() -> None:
    other = "So11111111111111111111111111111111111111112"
    text = f"{CHADIMALS_MINT} or {other}"
    assert extract_solana_mint_from_text(text) == CHADIMALS_MINT


def test_extract_whole_message_with_bom() -> None:
    assert extract_solana_mint_from_text("\ufeff" + CHADIMALS_MINT) == CHADIMALS_MINT
