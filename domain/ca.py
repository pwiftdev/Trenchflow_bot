import re

import base58

# Solana base58 mints: 32–44 chars; excludes 0 O I l.
_SOLANA_ADDRESS_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def is_valid_solana_address(address: str) -> bool:
    address = address.strip()
    if not _SOLANA_ADDRESS_RE.match(address):
        return False
    try:
        decoded = base58.b58decode(address)
    except ValueError:
        return False
    return len(decoded) == 32
