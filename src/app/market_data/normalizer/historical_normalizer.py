"""Normalize broker historical data."""

from app.brokers.shared.models import HistoricalBar as BrokerHistoricalBar
from app.market_data.models import HistoricalBar


def normalize_historical_bar(
    broker_bar: BrokerHistoricalBar,
    *,
    symbol: str,
    exchange: str,
) -> HistoricalBar:
    """Convert broker historical bar to enterprise model."""
    return HistoricalBar(
        symbol=symbol,
        exchange=exchange,
        timestamp=broker_bar.timestamp,
        open=broker_bar.open,
        high=broker_bar.high,
        low=broker_bar.low,
        close=broker_bar.close,
        volume=broker_bar.volume,
        open_interest=broker_bar.open_interest,
    )


def normalize_historical_bars(
    broker_bars: list[BrokerHistoricalBar],
    *,
    symbol: str,
    exchange: str,
) -> list[HistoricalBar]:
    """Convert broker historical bars."""
    return [
        normalize_historical_bar(bar, symbol=symbol, exchange=exchange)
        for bar in broker_bars
    ]
