"""Mock tick generator for tests."""

from datetime import datetime, timezone
from decimal import Decimal

from app.market_data.models.quote import OHLC
from app.market_data.models.tick import TickSnapshot


class MockTickGenerator:
    """Generate synthetic ticks for unit tests."""

    def __init__(self, symbol: str = "NIFTY", exchange: str = "NSE") -> None:
        """Initialize generator."""
        self._symbol = symbol
        self._exchange = exchange
        self._price = Decimal("22000")

    def next_tick(self, *, delta: Decimal = Decimal("1")) -> TickSnapshot:
        """Return next synthetic tick."""
        self._price += delta
        return TickSnapshot(
            symbol=self._symbol,
            exchange=self._exchange,
            ltp=self._price,
            ohlc=OHLC(
                open=self._price - delta,
                high=self._price,
                low=self._price - delta * 2,
                close=self._price,
            ),
            volume=1000,
            bid=self._price - Decimal("0.5"),
            ask=self._price + Decimal("0.5"),
            change=delta,
            change_percent=Decimal("0.01"),
            timestamp=datetime.now(timezone.utc),
        )
