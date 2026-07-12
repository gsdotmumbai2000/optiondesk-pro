"""Market data event publisher."""

from app.events.event_bus import EventBus
from app.market_data.events import (
    FutureUpdatedEvent,
    MarketClosedEvent,
    MarketOpenedEvent,
    OptionChainUpdatedEvent,
    QuoteUpdatedEvent,
    SnapshotUpdatedEvent,
)
from app.market_data.models import FutureQuote, MarketSnapshot, OptionChain, Quote


class MarketPublisher:
    """Publish normalized market data events."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize publisher."""
        self._event_bus = event_bus

    def publish_quote(self, quote: Quote) -> None:
        """Publish quote update."""
        self._publish(QuoteUpdatedEvent(payload={"quote": quote.model_dump()}))

    def publish_future(self, quote: FutureQuote) -> None:
        """Publish future update."""
        self._publish(FutureUpdatedEvent(payload={"future": quote.model_dump()}))

    def publish_option_chain(self, chain: OptionChain) -> None:
        """Publish option chain update."""
        self._publish(OptionChainUpdatedEvent(payload={"chain": chain.model_dump()}))

    def publish_snapshot(self, snapshot: MarketSnapshot) -> None:
        """Publish snapshot update."""
        self._publish(
            SnapshotUpdatedEvent(payload={"snapshot_id": snapshot.snapshot_id})
        )

    def publish_market_opened(self, exchange: str) -> None:
        """Publish market opened."""
        self._publish(MarketOpenedEvent(payload={"exchange": exchange}))

    def publish_market_closed(self, exchange: str) -> None:
        """Publish market closed."""
        self._publish(MarketClosedEvent(payload={"exchange": exchange}))

    def _publish(self, event: object) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)
