"""Enterprise live market data engine entry point."""

from pathlib import Path

from app.brokers.broker_interface.interface import BrokerInterface
from app.events.event_bus import EventBus
from app.market_data.providers.live_market_provider import LiveMarketDataProvider
from app.market_data.services.bundle import MarketDataServiceBundle


class LiveMarketDataEngine:
    """Facade for enterprise live market data components."""

    def __init__(
        self,
        broker: BrokerInterface,
        data_directory: Path,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize engine."""
        self._provider = LiveMarketDataProvider(broker, data_directory, event_bus)
        self.bundle = MarketDataServiceBundle.from_provider(self._provider)

    @property
    def provider(self) -> LiveMarketDataProvider:
        """Return underlying provider."""
        return self._provider

    def start(self) -> None:
        """Start engine."""
        self._provider.start()

    def stop(self) -> None:
        """Stop engine."""
        self._provider.stop()
