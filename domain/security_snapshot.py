from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SecuritySnapshot:
  """On-chain security fields (Helius). Optional fields are omitted from the card when None."""

  mint_renounced: Optional[bool] = None
  freeze_renounced: Optional[bool] = None
  top10_holder_pct: Optional[float] = None
  holder_count: Optional[int] = None
  supply_ui: Optional[str] = None
  fresh_1d_pct: Optional[float] = None
  fresh_7d_pct: Optional[float] = None
  dev_sold_label: Optional[str] = None
