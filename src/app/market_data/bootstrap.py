"""Market data bootstrap."""

from pathlib import Path

from app.brokers.broker_interface.interface import BrokerInterface
from app.events.event_bus import EventBus
from app.market_data.engine.live_engine import LiveMarketDataEngine
from app.market_data.services.bundle import MarketDataServiceBundle
from app.market_data.services.market_data_service import MarketDataService


class MarketDataProvider:
    """Factory for enterprise live market data engine."""

    def __init__(
        self,
        broker: BrokerInterface,
        data_directory: Path,
        event_bus: EventBus | None = None,
        instrument_service: object | None = None,
    ) -> None:
        """Initialize provider."""
        self._engine = LiveMarketDataEngine(
            broker,
            data_directory,
            event_bus,
            instrument_service=instrument_service,
        )
        self.engine = self._engine.provider.engine
        self.service: MarketDataService = self._engine.bundle.market_data
        self.bundle: MarketDataServiceBundle = self._engine.bundle
        self.dispatcher = self._engine.provider.dispatcher

    def start(self) -> None:
        """Start market data engine."""
        self._engine.start()

    def stop(self) -> None:
        """Stop market data engine."""
        self._engine.stop()
