"""Shared market data helpers for workspace services."""

from decimal import Decimal

from app.application.ports.market_data_port import MarketDataPort
from app.market_data.models.tick import TickSnapshot


class MarketDataSupport:
    """Mixin-style helper for workspace services."""

    def __init__(self, market_data: MarketDataPort | None = None) -> None:
        self._market_data = market_data

    def latest_price(self, symbol: str, exchange: str = "NSE") -> Decimal | None:
        """Return latest price via market data engine."""
        if self._market_data is None:
            return None
        return self._market_data.latest_price(symbol, exchange)

    def latest_tick(self, symbol: str, exchange: str = "NSE") -> TickSnapshot | None:
        """Return latest tick via market data engine."""
        if self._market_data is None:
            return None
        return self._market_data.latest_tick(symbol, exchange)

    def is_market_connected(self) -> bool:
        """Return whether live market data is connected."""
        if self._market_data is None:
            return False
        return self._market_data.connection_status().value == "Connected"
