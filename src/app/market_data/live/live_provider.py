"""Live market data provider orchestrator."""

from pathlib import Path

from app.brokers.broker_interface.interface import BrokerInterface
from app.brokers.events import BrokerConnectedEvent
from app.brokers.shared.models import Quote as BrokerQuote
from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger
from app.market_data.engine.market_data_engine import MarketDataEngine
from app.market_data.events import TickReceivedEvent
from app.market_data.live.heartbeat_monitor import HeartbeatMonitor
from app.market_data.live.market_status_detector import MarketStatusDetector
from app.market_data.live.reconnect_manager import ReconnectManager
from app.market_data.live.subscription_manager import MarketDataSubscriptionManager
from app.market_data.live.tick_cache import TickCache
from app.market_data.live.tick_dispatcher import TickDispatcher
from app.market_data.live.websocket_manager import WebSocketManager
from app.market_data.normalizer.quote_normalizer import normalize_quote
from app.market_data.publisher.market_publisher import MarketPublisher
from app.market_data.repository.market_data_repository import MarketDataRepository
from app.utils.constants import DATABASE_MARKET

logger = get_logger(__name__)


class LiveMarketDataProvider:
    """Orchestrate live feed, cache, and engine integration."""

    def __init__(
        self,
        broker: BrokerInterface,
        data_directory: Path,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize live market data provider."""
        repository = MarketDataRepository(data_directory / DATABASE_MARKET)
        self.engine = MarketDataEngine(broker, event_bus, repository)
        self.tick_cache = TickCache()
        self.dispatcher = TickDispatcher(self.tick_cache, event_bus)
        self.websocket = WebSocketManager(broker, self.dispatcher, event_bus)
        self.subscriptions = MarketDataSubscriptionManager(broker, event_bus)
        self.reconnect = ReconnectManager(self.websocket, self.subscriptions, event_bus)
        self.heartbeat = HeartbeatMonitor(self.websocket)
        self.market_status = MarketStatusDetector(broker, self.websocket)
        self._publisher = MarketPublisher(event_bus)
        self._event_bus = event_bus
        self._broker = broker
        from app.market_data.services.market_data_service import MarketDataService

        self.service = MarketDataService(self)
        self._last_market_status = None
        self._feed_started = False

    def start(self) -> None:
        """Start live market data pipeline."""
        self.engine.initialize()
        self._subscribe_engine_bridge()
        if self._broker.is_connected():
            self._start_feed()
        elif self._event_bus is not None:
            self._event_bus.subscribe(BrokerConnectedEvent, self._on_broker_ready)
        logger.info("Live market data provider started")

    def stop(self) -> None:
        """Stop live market data pipeline."""
        self.heartbeat.stop()
        self.websocket.disconnect()
        self.engine.shutdown()
        logger.info("Live market data provider stopped")

    def _start_feed(self) -> None:
        if self._feed_started:
            return
        self._feed_started = True
        self.websocket.connect()
        self.subscriptions.subscribe_defaults()
        self.heartbeat.start()
        self._publish_market_status()

    def _on_broker_ready(self, _event: BrokerConnectedEvent) -> None:
        self._start_feed()

    def _subscribe_engine_bridge(self) -> None:
        if self._event_bus is None:
            return
        self._event_bus.subscribe(TickReceivedEvent, self._on_tick_received)

    def _on_tick_received(self, event) -> None:
        payload = event.payload.get("tick", {})
        from app.market_data.models.tick import TickSnapshot

        tick = TickSnapshot.model_validate(payload)
        broker_quote = BrokerQuote(
            symbol=tick.symbol,
            exchange=tick.exchange,
            ltp=tick.ltp,
            open=tick.ohlc.open,
            high=tick.ohlc.high,
            low=tick.ohlc.low,
            close=tick.ohlc.close,
            bid=tick.bid,
            ask=tick.ask,
            volume=tick.volume,
            open_interest=tick.open_interest,
            change=tick.change,
            change_percent=tick.change_percent,
            timestamp=tick.timestamp,
        )
        quote = normalize_quote(broker_quote)
        self.engine.ingest_quote(quote)
        self._publish_market_status()

    def _publish_market_status(self) -> None:
        snapshot = self.market_status.detect()
        if self._last_market_status == snapshot.status:
            return
        self._last_market_status = snapshot.status
        if snapshot.status.value == "Open":
            self._publisher.publish_market_opened(snapshot.exchange)
        elif snapshot.status.value in {"Closed", "Holiday"}:
            self._publisher.publish_market_closed(snapshot.exchange)
