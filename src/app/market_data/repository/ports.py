"""Market data repository port."""

from typing import Protocol

from app.market_data.models import HistoricalBar, MarketStatistics


class IMarketDataRepository(Protocol):
    """Persistence port for market data."""

    def initialize(self) -> None: ...

    def close(self) -> None: ...

    def save_bars(self, bars: list[HistoricalBar]) -> None: ...

    def load_bars(self, symbol: str, exchange: str, limit: int = 500) -> list[HistoricalBar]: ...

    def save_statistics(self, stats: MarketStatistics) -> None: ...

    def load_statistics(self, symbol: str, exchange: str) -> MarketStatistics | None: ...
