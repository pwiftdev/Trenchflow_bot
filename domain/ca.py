import re
from typing import Optional

import base58

# Solana base58 mints: 32–44 chars; excludes 0 O I l.
_SOLANA_ADDRESS_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
_CANDIDATE_IN_TEXT_RE = re.compile(
    r"(?<![1-9A-HJ-NP-Za-km-z])([1-9A-HJ-NP-Za-km-z]{32,44})(?![1-9A-HJ-NP-Za-km-z])"
)


def is_valid_solana_address(address: str) -> bool:
    address = address.strip()
    if not _SOLANA_ADDRESS_RE.match(address):
        return False
    try:
        decoded = base58.b58decode(address)
    except ValueError:
        return False
    return len(decoded) == 32


def extract_solana_mint_from_text(text: str) -> Optional[str]:
    """Return the first valid Solana mint found in free-form message text."""
    for match in _CANDIDATE_IN_TEXT_RE.finditer(text):
        candidate = match.group(1)
        if is_valid_solana_address(candidate):
            return candidate
    return None
