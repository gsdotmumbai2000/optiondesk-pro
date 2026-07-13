"""WebSocket lifecycle for live market data."""

from datetime import datetime, timezone
from threading import RLock
from typing import Any

from app.brokers.broker_interface.interface import BrokerInterface
from app.brokers.breeze.normalizers.quote_normalizer import normalize_quote as breeze_quote
from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger
from app.market_data.diagnostics import log_tick_diagnostic
from app.market_data.dispatcher.event_dispatcher import EventDispatcher
from app.market_data.models.quote import OHLC
from app.market_data.models.tick import TickSnapshot
from app.market_data.websocket.enums import LiveConnectionStatus

logger = get_logger(__name__)


class WebSocketService:
    """Manage single broker websocket connection for live ticks."""

    def __init__(
        self,
        broker: BrokerInterface,
        dispatcher: EventDispatcher,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize websocket service."""
        self._broker = broker
        self._dispatcher = dispatcher
        self._event_bus = event_bus
        self._lock = RLock()
        self._status = LiveConnectionStatus.DISCONNECTED
        self._last_message: datetime | None = None

    @property
    def status(self) -> LiveConnectionStatus:
        """Return websocket connection status."""
        with self._lock:
            return self._status

    @property
    def last_message(self) -> datetime | None:
        """Return last websocket message time."""
        with self._lock:
            return self._last_message

    def connect(self) -> None:
        """Connect websocket feed via broker."""
        if not self._broker.is_connected():
            return
        with self._lock:
            self._status = LiveConnectionStatus.CONNECTING
        self._attach_handler()
        with self._lock:
            self._status = LiveConnectionStatus.CONNECTED
        logger.info("Market data websocket connected")

    def disconnect(self) -> None:
        """Disconnect websocket feed."""
        with self._lock:
            self._status = LiveConnectionStatus.DISCONNECTED
        logger.info("Market data websocket disconnected")

    def on_broker_connected(self) -> None:
        """Handle broker reconnect."""
        self._attach_handler()
        with self._lock:
            self._status = LiveConnectionStatus.CONNECTED

    def on_broker_disconnected(self) -> None:
        """Handle broker disconnect."""
        with self._lock:
            self._status = LiveConnectionStatus.DISCONNECTED

    def _attach_handler(self) -> None:
        websocket = getattr(self._broker, "_websocket", None)
        if websocket is None:
            return
        websocket.set_quote_handler(self._on_raw_ticks)

    def _on_raw_ticks(self, payload: Any) -> None:
        ticks = payload if isinstance(payload, list) else [payload]
        for item in ticks:
            self._process_tick(item)

    def _process_tick(self, item: Any) -> None:
        if not isinstance(item, dict):
            return
        symbol = str(item.get("stock_code") or item.get("symbol") or "")
        exchange = str(item.get("exchange_code") or item.get("exchange") or "NSE")
        if not symbol:
            return
        broker_quote = breeze_quote(symbol, exchange, item)
        tick = TickSnapshot(
            symbol=broker_quote.symbol,
            exchange=broker_quote.exchange,
            ltp=broker_quote.ltp,
            ohlc=OHLC(
                open=broker_quote.open,
                high=broker_quote.high,
                low=broker_quote.low,
                close=broker_quote.close,
            ),
            volume=broker_quote.volume,
            open_interest=broker_quote.open_interest,
            bid=broker_quote.bid,
            ask=broker_quote.ask,
            change=broker_quote.change,
            timestamp=broker_quote.timestamp,
            product_type=str(item.get("product_type", "")),
            expiry_date=str(item.get("expiry_date", "")),
            strike_price=str(item.get("strike_price", "")),
            option_right=str(item.get("right", "")),
        )
        self._dispatcher.enqueue(tick)
        log_tick_diagnostic(logger, "WEBSOCKET", "tick received", tick)
        with self._lock:
            self._last_message = datetime.now(timezone.utc)
