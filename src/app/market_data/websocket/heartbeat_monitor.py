"""Heartbeat monitor for live websocket feed."""

from datetime import datetime, timedelta, timezone
from threading import Event, Thread

from app.logging.logging_manager import get_logger
from app.market_data.websocket.websocket_service import WebSocketService

logger = get_logger(__name__)


class HeartbeatMonitor:
    """Detect stale websocket feeds on a background thread."""

    def __init__(
        self,
        websocket: WebSocketService,
        *,
        interval_sec: int = 30,
        stale_sec: int = 120,
    ) -> None:
        """Initialize heartbeat monitor."""
        self._websocket = websocket
        self._interval_sec = interval_sec
        self._stale_sec = stale_sec
        self._stop = Event()
        self._thread: Thread | None = None
        self._stale = False

    @property
    def is_stale(self) -> bool:
        """Return whether feed is stale."""
        return self._stale

    def start(self) -> None:
        """Start background heartbeat monitor."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = Thread(target=self._loop, name="md-heartbeat", daemon=True)
        self._thread.start()
        logger.info("Market data heartbeat monitor started")

    def stop(self) -> None:
        """Stop heartbeat monitor."""
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _loop(self) -> None:
        while not self._stop.wait(self._interval_sec):
            self._check()

    def _check(self) -> None:
        last = self._websocket.last_message
        if last is None:
            return
        age = datetime.now(timezone.utc) - last
        stale = age > timedelta(seconds=self._stale_sec)
        if stale and not self._stale:
            logger.warning("Market data heartbeat stale ({seconds}s)", seconds=age.seconds)
        self._stale = stale
