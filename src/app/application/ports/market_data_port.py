"""Market data port for application workspaces."""

from decimal import Decimal
from typing import Protocol

from app.market_data.models.tick import TickSnapshot
from app.market_data.models.live_status import MarketStatusSnapshot
from app.market_data.websocket.connection_state import MarketDataConnectionState


class MarketDataPort(Protocol):
    """Read-only live market data access for ViewModels."""

    def latest_price(self, symbol: str, exchange: str, **parts: str) -> Decimal | None:
        """Return latest traded price."""

    def latest_tick(self, symbol: str, exchange: str, **parts: str) -> TickSnapshot | None:
        """Return latest tick snapshot."""

    def market_status(self) -> MarketStatusSnapshot:
        """Return current market status."""

    def connection_status(self) -> MarketDataConnectionState:
        """Return connection state."""
