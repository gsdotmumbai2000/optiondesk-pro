"""Breeze websocket manager."""

import traceback
from threading import RLock
from typing import Any, Callable

from app.brokers.breeze.client_port import BreezeClientPort
from app.brokers.breeze.feed_subscription import (
    build_subscribe_feed_kwargs,
    build_unsubscribe_feed_kwargs,
)
from app.brokers.breeze.normalizers.quote_normalizer import normalize_quote
from app.brokers.events import OptionChainUpdatedEvent, QuoteUpdatedEvent
from app.brokers.shared.models import OptionChainRequest, QuoteSubscription
from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger

logger = get_logger(__name__)


class BreezeWebSocket:
    """Manage Breeze websocket subscriptions."""

    def __init__(
        self,
        client: BreezeClientPort,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize websocket manager."""
        self._client = client
        self._event_bus = event_bus
        self._lock = RLock()
        self._connected = False
        self._pending_ws_connect = False
        self._quote_subscriptions: list[QuoteSubscription] = []
        self._chain_subscriptions: list[OptionChainRequest] = []
        self._user_quote_handler: Callable[[Any], None] | None = None
        self._install_sdk_callback()

    @property
    def is_connected(self) -> bool:
        """Return websocket connection state."""
        with self._lock:
            return self._connected

    def connect(self) -> None:
        """Connect websocket feed after quote callback is registered."""
        with self._lock:
            self._pending_ws_connect = True
            self._try_ws_connect()

    def disconnect(self) -> None:
        """Disconnect websocket feed."""
        with self._lock:
            self._client.ws_disconnect()
            self._connected = False
            self._pending_ws_connect = False

    def subscribe_quotes(self, subscription: QuoteSubscription) -> None:
        """Subscribe to quote feed."""
        with self._lock:
            self._install_sdk_callback()
            self._try_ws_connect()
            kwargs = build_subscribe_feed_kwargs(subscription)
            symbol = subscription.symbol
            exchange = subscription.exchange
            logger.info(
                "Subscribing {symbol}@{exchange}",
                symbol=symbol,
                exchange=exchange,
            )
            result = self._call_subscribe_feeds(kwargs)
            self._raise_if_feed_call_failed(result)
            logger.info(
                "Subscription successful: {symbol}@{exchange}",
                symbol=symbol,
                exchange=exchange,
            )
            if subscription not in self._quote_subscriptions:
                self._quote_subscriptions.append(subscription)

    def unsubscribe_quotes(self, subscription: QuoteSubscription) -> None:
        """Unsubscribe from quote feed."""
        with self._lock:
            kwargs = build_unsubscribe_feed_kwargs(subscription)
            symbol = subscription.symbol
            exchange = subscription.exchange
            logger.info(
                "Unsubscribing {symbol}@{exchange} with kwargs: {kwargs}",
                symbol=symbol,
                exchange=exchange,
                kwargs=kwargs,
            )
            try:
                result = self._client.unsubscribe_feeds(**kwargs)
                self._raise_if_feed_call_failed(result)
            except Exception as error:
                logger.error(
                    "Unsubscribe failed: {symbol}@{exchange} kwargs={kwargs} error={error}\n{traceback}",
                    symbol=symbol,
                    exchange=exchange,
                    kwargs=kwargs,
                    error=error,
                    traceback=traceback.format_exc(),
                )
                raise
            self._quote_subscriptions = [
                item
                for item in self._quote_subscriptions
                if item != subscription
            ]

    def subscribe_option_chain(self, request: OptionChainRequest) -> None:
        """Track option chain subscription for resubscribe."""
        with self._lock:
            self._chain_subscriptions.append(request)

    def unsubscribe_option_chain(self, request: OptionChainRequest) -> None:
        """Remove option chain subscription."""
        with self._lock:
            self._chain_subscriptions = [
                item
                for item in self._chain_subscriptions
                if item.expiry_date != request.expiry_date
            ]

    def resubscribe_all(self) -> None:
        """Resubscribe all feeds after reconnect."""
        with self._lock:
            for subscription in list(self._quote_subscriptions):
                self.subscribe_quotes(subscription)

    def publish_quote(self, symbol: str, exchange: str, payload: Any) -> None:
        """Publish normalized quote update."""
        if self._event_bus is None:
            return
        quote = normalize_quote(symbol, exchange, payload)
        self._event_bus.publish(
            QuoteUpdatedEvent(payload={"symbol": symbol, "quote": quote.model_dump()})
        )

    def publish_option_chain(self, chain_payload: dict[str, Any]) -> None:
        """Publish option chain update event."""
        if self._event_bus is None:
            return
        self._event_bus.publish(OptionChainUpdatedEvent(payload=chain_payload))

    def set_quote_handler(self, handler: Callable[[Any], None]) -> None:
        """Register application quote handler and connect websocket if pending."""
        with self._lock:
            self._user_quote_handler = handler
            self._install_sdk_callback()
            self._try_ws_connect()

    def _install_sdk_callback(self) -> None:
        """Bind BreezeConnect.on_ticks to the SDK entry wrapper."""
        if not hasattr(self._client, "on_ticks"):
            logger.warning("Breeze client does not expose on_ticks callback property")
            return
        current = getattr(self._client, "on_ticks", None)
        if current is self._on_sdk_ticks:
            return
        setattr(self._client, "on_ticks", self._on_sdk_ticks)
        logger.info("Breeze on_ticks callback registered on SDK client")

    def _on_sdk_ticks(self, data: Any) -> None:
        """SDK entry point invoked by BreezeConnect SocketEventBreeze.on_message."""
        logger.info("RAW SDK CALLBACK RECEIVED")
        handler = self._user_quote_handler
        if handler is None:
            logger.warning("RAW SDK CALLBACK RECEIVED but no quote handler is registered")
            return
        try:
            handler(data)
        except Exception as error:
            logger.error(
                "Quote handler failed: {error}\n{traceback}",
                error=error,
                traceback=traceback.format_exc(),
            )

    def _try_ws_connect(self) -> None:
        """Open websocket only after the SDK callback and user handler are ready."""
        if self._connected or not self._pending_ws_connect:
            return
        if self._user_quote_handler is None:
            logger.debug("Deferring Breeze ws_connect until quote handler is registered")
            return
        self._install_sdk_callback()
        self._client.ws_connect()
        self._connected = True
        logger.info("Breeze websocket connected")

    def _call_subscribe_feeds(self, kwargs: dict[str, Any]) -> Any:
        """Call Breeze subscribe_feeds with diagnostic logging."""

        logger.info("subscribe_feeds kwargs: {kwargs}", kwargs=kwargs)

        sdk_kwargs = dict(kwargs)

        exchange_code = sdk_kwargs.get("exchange_code")
        if isinstance(exchange_code, str):
            sdk_kwargs["exchange_code"] = exchange_code.upper()

        logger.info("subscribe_feeds sdk_kwargs: {kwargs}", kwargs=sdk_kwargs)

        try:
            return self._client.subscribe_feeds(**sdk_kwargs)
        except Exception as error:
            logger.error(
                "subscribe_feeds failed: exception_type={exception_type} kwargs={kwargs}\n{traceback}",
                exception_type=type(error).__name__,
                kwargs=sdk_kwargs,
                traceback=traceback.format_exc(),
            )
            raise

    @staticmethod
    def _raise_if_feed_call_failed(result: Any) -> None:
        """Raise when Breeze SDK returns an error string instead of a dict."""
        if isinstance(result, str):
            raise RuntimeError(result)
