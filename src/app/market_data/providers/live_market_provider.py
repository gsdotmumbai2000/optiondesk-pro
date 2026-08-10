"""Enterprise live market data provider."""

from pathlib import Path

from app.brokers.broker_interface.interface import BrokerInterface
from app.brokers.shared.models import Quote as BrokerQuote
from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger
from app.market_data.dispatcher.event_dispatcher import EventDispatcher
from app.market_data.engine.market_data_engine import MarketDataEngine
from app.market_data.events import TickReceivedEvent
from app.market_data.normalizer.quote_normalizer import normalize_quote
from app.market_data.providers.market_status_detector import MarketStatusDetector
from app.market_data.publisher.market_publisher import MarketPublisher
from app.market_data.repository.market_data_repository import MarketDataRepository
from app.market_data.services.market_cache_service import MarketCacheService
from app.market_data.services.market_data_service import MarketDataService
from app.market_data.services.reconnect_service import ReconnectService
from app.market_data.subscriptions.subscription_service import SubscriptionService
from app.market_data.symbols import InstrumentMasterSymbolCanonicalizer
from app.market_data.websocket.connection_state import ConnectionStateMachine
from app.market_data.websocket.heartbeat_monitor import HeartbeatMonitor
from app.market_data.websocket.websocket_service import WebSocketService
from app.utils.constants import DATABASE_MARKET

logger = get_logger(__name__)


class LiveMarketDataProvider:
    """Single orchestrator for enterprise live market data."""

    def __init__(
        self,
        broker: BrokerInterface,
        data_directory: Path,
        event_bus: EventBus | None = None,
        instrument_service: object | None = None,
    ) -> None:
        """Initialize live market data provider."""
        repository = MarketDataRepository(data_directory / DATABASE_MARKET)
        self.engine = MarketDataEngine(broker, event_bus, repository)
        self.connection = ConnectionStateMachine(event_bus)
        self.cache = MarketCacheService()
        self.dispatcher = EventDispatcher(
            self.cache,
            event_bus,
            can_dispatch=self.connection.can_subscribe,
        )
        self.websocket = WebSocketService(
            broker,
            self.dispatcher,
            event_bus,
            symbol_canonicalizer=InstrumentMasterSymbolCanonicalizer(instrument_service),
        )
        self.subscriptions = SubscriptionService(
            broker,
            event_bus,
            can_subscribe=self.connection.can_subscribe,
        )
        self.heartbeat = HeartbeatMonitor(self.websocket)
        self.reconnect = ReconnectService(
            self.connection,
            self.websocket,
            self.subscriptions,
            self.heartbeat,
            event_bus,
        )
        self.market_status = MarketStatusDetector(broker, self.websocket)
        self._publisher = MarketPublisher(event_bus)
        self._event_bus = event_bus
        self._broker = broker
        self._last_market_status = None
        self.service = MarketDataService(self)
        self.connection.on_connected(self._activate_live_feed)
        self.connection.on_disconnected(self._pause_live_feed)

    @property
    def tick_cache(self):
        """Backward-compatible tick cache accessor."""
        return self.cache.live

    def start(self) -> None:
        """Start live market data pipeline without broker subscriptions."""
        self.engine.initialize()
        self._subscribe_engine_bridge()
        self.subscriptions.register_defaults()
        self.connection.start()
        self.reconnect.start()
        logger.info("Enterprise live market data engine started")

    def stop(self) -> None:
        """Stop live market data pipeline."""
        self._pause_live_feed()
        self.reconnect.stop()
        self.dispatcher.shutdown()
        self.engine.shutdown()
        logger.info("Enterprise live market data engine stopped")

    def _activate_live_feed(self) -> None:
        """Connect websocket and activate pending subscriptions."""
        self.websocket.connect()
        self.subscriptions.activate_pending()
        self.heartbeat.start()
        self._publish_market_status()

    def _pause_live_feed(self) -> None:
        """Pause live feed and retain cached prices."""
        self.heartbeat.stop()
        self.subscriptions.deactivate_all()
        self.websocket.disconnect()

    def _subscribe_engine_bridge(self) -> None:
        if self._event_bus is None:
            return
        self._event_bus.subscribe(TickReceivedEvent, self._on_tick_received)

    def _on_tick_received(self, event: TickReceivedEvent) -> None:
        if not self.connection.is_connected:
            return
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
