"""Reconnect service with exponential backoff."""

from threading import Event, Thread

from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger
from app.market_data.events import ReconnectCompletedEvent, ReconnectStartedEvent
from app.market_data.subscriptions.subscription_service import SubscriptionService
from app.market_data.websocket.connection_state import ConnectionStateMachine
from app.market_data.websocket.heartbeat_monitor import HeartbeatMonitor
from app.market_data.websocket.websocket_service import WebSocketService

logger = get_logger(__name__)


class ReconnectService:
    """Recover websocket feed with exponential backoff."""

    def __init__(
        self,
        connection: ConnectionStateMachine,
        websocket: WebSocketService,
        subscriptions: SubscriptionService,
        heartbeat: HeartbeatMonitor,
        event_bus: EventBus | None = None,
        *,
        backoff_seconds: tuple[int, ...] = (1, 2, 4, 8, 16, 30),
    ) -> None:
        """Initialize reconnect service."""
        self._connection = connection
        self._websocket = websocket
        self._subscriptions = subscriptions
        self._heartbeat = heartbeat
        self._event_bus = event_bus
        self._backoff = backoff_seconds
        self._attempt = 0
        self._stop = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        """Start reconnect monitor thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = Thread(target=self._monitor, name="md-reconnect", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop reconnect monitor."""
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def recover_now(self) -> None:
        """Attempt immediate recovery."""
        self._attempt_reconnect()

    def _monitor(self) -> None:
        while not self._stop.wait(5):
            if not self._heartbeat.is_stale:
                continue
            if not self._connection.is_connected:
                continue
            self._schedule_reconnect()

    def _schedule_reconnect(self) -> None:
        delay = self._backoff[min(self._attempt, len(self._backoff) - 1)]
        self._attempt += 1
        self._publish(ReconnectStartedEvent(payload={"delay_seconds": delay}))
        logger.warning("Scheduling market data reconnect in {delay}s", delay=delay)
        if self._stop.wait(delay):
            return
        self._attempt_reconnect()

    def _attempt_reconnect(self) -> None:
        try:
            self._websocket.connect()
            self._subscriptions.resubscribe_all()
            self._attempt = 0
            self._publish(ReconnectCompletedEvent(payload={}))
            logger.info("Market data reconnect completed")
        except Exception as error:
            logger.warning("Market data reconnect failed: {error}", error=error)

    def _publish(self, event: object) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)
