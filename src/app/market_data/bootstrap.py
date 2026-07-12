"""Market data bootstrap."""

from pathlib import Path

from app.brokers.broker_interface.interface import BrokerInterface
from app.events.event_bus import EventBus
from app.market_data.live.live_provider import LiveMarketDataProvider
from app.market_data.services.market_data_service import MarketDataService


class MarketDataProvider:
    """Factory for live market data engine."""

    def __init__(
        self,
        broker: BrokerInterface,
        data_directory: Path,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize provider."""
        self._live = LiveMarketDataProvider(broker, data_directory, event_bus)
        self.engine = self._live.engine
        self.service: MarketDataService = self._live.service

    def start(self) -> None:
        """Start market data engine."""
        self._live.start()

    def stop(self) -> None:
        """Stop market data engine."""
        self._live.stop()
