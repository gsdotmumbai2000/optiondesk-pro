"""Reconnect handling for live market data."""

from app.brokers.events import BrokerConnectedEvent, BrokerDisconnectedEvent
from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger
from app.market_data.live.subscription_manager import MarketDataSubscriptionManager
from app.market_data.live.websocket_manager import WebSocketManager

logger = get_logger(__name__)


class ReconnectManager:
    """Recover subscriptions after broker reconnect."""

    def __init__(
        self,
        websocket: WebSocketManager,
        subscriptions: MarketDataSubscriptionManager,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize reconnect manager."""
        self._websocket = websocket
        self._subscriptions = subscriptions
        self._event_bus = event_bus
        if event_bus is not None:
            event_bus.subscribe(BrokerConnectedEvent, self._on_connected)
            event_bus.subscribe(BrokerDisconnectedEvent, self._on_disconnected)

    def _on_connected(self, _event: BrokerConnectedEvent) -> None:
        logger.info("Broker connected — recovering market data subscriptions")
        self._websocket.on_broker_connected()
        self._subscriptions.resubscribe_all()

    def _on_disconnected(self, _event: BrokerDisconnectedEvent) -> None:
        logger.warning("Broker disconnected — live feed paused")
        self._websocket.on_broker_disconnected()
