"""Broker historical data port for application workspaces."""

from datetime import datetime
from typing import Protocol

from app.backtesting.models.historical import HistoricalMarketData


class BrokerHistoricalPort(Protocol):
    """On-demand real-broker historical bars lookup for backtesting."""

    def get_historical_bars(
        self,
        underlying: str,
        exchange: str,
        from_date: datetime,
        to_date: datetime,
    ) -> HistoricalMarketData | None:
        """Return real historical bars for the underlying, or None when
        unavailable (no broker connected, broker doesn't support it, or the
        call failed) -- callers should treat that as "no data", not as an
        error."""
