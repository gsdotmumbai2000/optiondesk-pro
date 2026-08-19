"""Bridges BrokerInterface.get_historical_data() (broker-shared
HistoricalBar, no symbol/exchange) into the backtesting engine's
HistoricalMarketData (domain HistoricalBar, symbol/exchange attached), for
on-demand backtest runs against real broker history -- a single REST call
per run, not a live/streaming source.
"""

from datetime import datetime

from app.backtesting.models.historical import HistoricalMarketData
from app.brokers.bootstrap import BrokerProvider
from app.brokers.shared.enums import HistoricalInterval, ProductType
from app.brokers.shared.exceptions import BrokerNotSupportedException
from app.brokers.shared.models import HistoricalRequest
from app.exceptions.broker_exception import BrokerException
from app.market_data.models.snapshot import HistoricalBar


class BrokerHistoricalAdapter:
    """BrokerHistoricalPort implementation backed by a live BrokerInterface."""

    def __init__(self, broker_provider: BrokerProvider) -> None:
        self._broker_provider = broker_provider

    def get_historical_bars(
        self,
        underlying: str,
        exchange: str,
        from_date: datetime,
        to_date: datetime,
    ) -> HistoricalMarketData | None:
        """Return real historical daily bars for the underlying, or None on
        any failure (not connected, broker doesn't support it, API error, or
        no bars for the period) so callers can fall back to "nothing to
        backtest" rather than a fabricated result."""
        broker = self._broker_provider.broker
        if broker is None or not broker.is_connected():
            return None
        request = HistoricalRequest(
            symbol=underlying,
            exchange=exchange,
            product_type=ProductType.CASH,
            interval=HistoricalInterval.ONE_DAY,
            from_date=from_date,
            to_date=to_date,
        )
        try:
            bars = broker.get_historical_data(request)
        except (BrokerNotSupportedException, BrokerException):
            return None
        if not bars:
            return None
        domain_bars = tuple(
            HistoricalBar(
                symbol=underlying,
                exchange=exchange,
                timestamp=bar.timestamp,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                open_interest=bar.open_interest,
            )
            for bar in bars
        )
        return HistoricalMarketData(underlying=underlying, exchange=exchange, bars=domain_bars)
