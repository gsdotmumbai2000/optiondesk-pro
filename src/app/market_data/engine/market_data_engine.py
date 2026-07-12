"""Enterprise market data engine."""

from datetime import datetime, timezone

from app.brokers.broker_interface.interface import BrokerInterface
from app.brokers.events import BrokerConnectedEvent, BrokerDisconnectedEvent, QuoteUpdatedEvent
from app.brokers.shared.models import Quote as BrokerQuote
from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger
from app.market_data.cache.keys import quote_key
from app.market_data.cache.market_cache import MarketCache
from app.market_data.events import QuoteUpdatedEvent as MdQuoteUpdatedEvent
from app.market_data.history.history_manager import HistoryManager
from app.market_data.models import MarketStatistics, Quote
from app.market_data.normalizer.quote_normalizer import normalize_quote, to_future_quote
from app.market_data.publisher.market_publisher import MarketPublisher
from app.market_data.repository.market_data_repository import MarketDataRepository
from app.market_data.services.query_service import MarketDataQueryService
from app.market_data.snapshots.snapshot_manager import SnapshotManager
from app.market_data.subscribers.subscriber_registry import SubscriberRegistry
from app.market_data.validation.validators import MarketDataValidator
from app.market_data.workers.coordinator import MarketDataWorkers

logger = get_logger(__name__)


class MarketDataEngine:
    """Central market data orchestrator."""

    def __init__(
        self,
        broker: BrokerInterface,
        event_bus: EventBus | None = None,
        repository: MarketDataRepository | None = None,
    ) -> None:
        """Initialize market data engine."""
        self._broker = broker
        self._event_bus = event_bus
        self._repository = repository
        self._cache = MarketCache()
        self._history = HistoryManager()
        self._snapshots = SnapshotManager()
        self._validator = MarketDataValidator()
        self._publisher = MarketPublisher(event_bus)
        self._subscribers = SubscriberRegistry()
        self._workers = MarketDataWorkers()
        self._query = MarketDataQueryService(
            broker,
            self._cache,
            self._history,
            self._snapshots,
            self._validator,
        )
        self._running = False

    @property
    def query(self) -> MarketDataQueryService:
        """Return query API."""
        return self._query

    @property
    def subscribers(self) -> SubscriberRegistry:
        """Return subscriber registry."""
        return self._subscribers

    def initialize(self) -> None:
        """Initialize engine subsystems."""
        if self._repository is not None:
            self._repository.initialize()
        if self._event_bus is not None:
            self._event_bus.subscribe(QuoteUpdatedEvent, self._on_broker_quote)
            self._event_bus.subscribe(BrokerConnectedEvent, self._on_broker_connected)
            self._event_bus.subscribe(BrokerDisconnectedEvent, self._on_broker_disconnected)
        self._workers.start()
        self._running = True
        logger.info("Market data engine initialized")

    def connect_to_broker(self) -> None:
        """Connect to broker if not connected."""
        if not self._broker.is_connected():
            self._broker.connect()
            self._broker.authenticate()

    def shutdown(self) -> None:
        """Shutdown engine."""
        self._workers.stop()
        if self._event_bus is not None:
            self._event_bus.unsubscribe(QuoteUpdatedEvent, self._on_broker_quote)
            self._event_bus.unsubscribe(BrokerConnectedEvent, self._on_broker_connected)
            self._event_bus.unsubscribe(BrokerDisconnectedEvent, self._on_broker_disconnected)
        if self._repository is not None:
            self._repository.close()
        self._running = False
        logger.info("Market data engine shutdown")

    def ingest_quote(self, quote: Quote) -> None:
        """Validate, cache, publish, and store a quote."""
        self._workers.quotes.submit(lambda: self._process_quote(quote))

    def capture_snapshot(self) -> None:
        """Capture market snapshot asynchronously."""
        self._workers.snapshot.submit(self._capture_snapshot_task)

    def cleanup_cache(self) -> None:
        """Purge expired cache entries."""
        self._workers.cleanup.submit(self._cleanup_task)

    def _process_quote(self, quote: Quote) -> None:
        self._validator.validate_quote(quote)
        self._cache.put_quote(quote)
        key = quote_key(quote.exchange, quote.symbol)
        self._history.add_quote(key, quote)
        self._publisher.publish_quote(quote)
        self._subscribers.notify(
            "quotes",
            MdQuoteUpdatedEvent(payload={"quote": quote.model_dump()}),
        )
        if quote.instrument_kind.value == "FUTURE":
            self._publisher.publish_future(to_future_quote(quote))
        self._persist_statistics(quote)

    def _capture_snapshot_task(self) -> None:
        quotes = {
            quote_key(q.exchange, q.symbol): q
            for q in self._cache.list_quotes()
        }
        snapshot = self._snapshots.capture(quotes)
        self._publisher.publish_snapshot(snapshot)

    def _cleanup_task(self) -> None:
        removed = self._cache.purge_expired()
        logger.debug("Purged {count} expired cache entries", count=removed)

    def _persist_statistics(self, quote: Quote) -> None:
        if self._repository is None:
            return
        stats = MarketStatistics(
            symbol=quote.symbol,
            exchange=quote.exchange,
            total_volume=quote.volume or 0,
            total_oi=quote.open_interest or 0,
            quote_count=1,
            updated_at=datetime.now(timezone.utc),
        )
        self._repository.save_statistics(stats)

    def _on_broker_quote(self, event: QuoteUpdatedEvent) -> None:
        payload = event.payload.get("quote", {})
        broker_quote = BrokerQuote.model_validate(payload)
        quote = normalize_quote(broker_quote)
        self.ingest_quote(quote)

    def _on_broker_connected(self, event: BrokerConnectedEvent) -> None:
        logger.info("Broker connected: {payload}", payload=event.payload)

    def _on_broker_disconnected(self, event: BrokerDisconnectedEvent) -> None:
        self._cache.invalidate_all()
        logger.info("Broker disconnected, cache invalidated")
