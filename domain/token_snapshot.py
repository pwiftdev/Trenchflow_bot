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
    price_change_h1: Optional[float]
    price_change_h24: Optional[float]
    txns_h1_buys: Optional[int]
    txns_h1_sells: Optional[int]
    pair_created_at_ms: Optional[int]
    dex_id: Optional[str]
    labels: list[str] = field(default_factory=list)
    pair_url: Optional[str] = None
    image_url: Optional[str] = None
    header_image_url: Optional[str] = None
    open_graph_url: Optional[str] = None
    websites: list[tuple[str, str]] = field(default_factory=list)
    socials: list[tuple[str, str]] = field(default_factory=list)
    boosts_active: Optional[int] = None
