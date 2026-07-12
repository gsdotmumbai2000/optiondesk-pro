"""Market data bootstrap."""

from pathlib import Path

from app.brokers.broker_interface.interface import BrokerInterface
from app.events.event_bus import EventBus
from app.market_data.engine.market_data_engine import MarketDataEngine
from app.market_data.repository.market_data_repository import MarketDataRepository
from app.utils.constants import DATABASE_MARKET


class MarketDataProvider:
    """Factory for market data engine."""

    def __init__(
        self,
        broker: BrokerInterface,
        data_directory: Path,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize provider."""
        repository = MarketDataRepository(data_directory / DATABASE_MARKET)
        self.engine = MarketDataEngine(broker, event_bus, repository)

    def start(self) -> None:
        """Start market data engine."""
        self.engine.initialize()
        self.engine.connect_to_broker()

    def stop(self) -> None:
        """Stop market data engine."""
        self.engine.shutdown()
