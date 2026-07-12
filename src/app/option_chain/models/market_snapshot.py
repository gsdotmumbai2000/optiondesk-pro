"""Option chain market snapshot."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ChainMarketSnapshot:
    """Market snapshot for option chain analytics."""

    snapshot_id: str
    underlying: str
    exchange: str
    spot_price: Decimal
    captured_at: datetime | None = None
