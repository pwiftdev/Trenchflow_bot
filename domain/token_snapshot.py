from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class TokenSnapshot:
    mint: str
    symbol: Optional[str]
    name: Optional[str]
    price_usd: Optional[float]
    market_cap: Optional[float]
    fdv: Optional[float]
    liquidity_usd: Optional[float]
    volume_h24: Optional[float]
    price_change_h24: Optional[float]
    dex_id: Optional[str]
    pair_url: Optional[str]
    image_url: Optional[str]
    websites: list[tuple[str, str]] = field(default_factory=list)
    socials: list[tuple[str, str]] = field(default_factory=list)
