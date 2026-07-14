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
        self._quote_subscriptions: list[QuoteSubscription] = []
        self._chain_subscriptions: list[OptionChainRequest] = []

    @property
    def is_connected(self) -> bool:
        """Return websocket connection state."""
        with self._lock:
            return self._connected

    def connect(self) -> None:
        """Connect websocket feed."""
        with self._lock:
            self._client.ws_connect()
            self._connected = True

    def disconnect(self) -> None:
        """Disconnect websocket feed."""
        with self._lock:
            self._client.ws_disconnect()
            self._connected = False

    def subscribe_quotes(self, subscription: QuoteSubscription) -> None:
        """Subscribe to quote feed."""
        with self._lock:
            kwargs = build_subscribe_feed_kwargs(subscription)
            symbol = subscription.symbol
            logger.info(
                "Calling subscribe_feeds with arguments: {kwargs}",
                kwargs=kwargs,
            )
            try:
                result = self._client.subscribe_feeds(**kwargs)
                self._raise_if_feed_call_failed(result)
            except Exception as error:
                logger.error(
                    "Subscription failed: {symbol} - {error}\n{traceback}",
                    symbol=symbol,
                    error=error,
                    traceback=traceback.format_exc(),
                )
                raise
            logger.info(
                "Subscription added: {symbol}@{exchange}",
                symbol=symbol,
                exchange=subscription.exchange,
            )
            if subscription not in self._quote_subscriptions:
                self._quote_subscriptions.append(subscription)

    def unsubscribe_quotes(self, subscription: QuoteSubscription) -> None:
        """Unsubscribe from quote feed."""
        with self._lock:
            kwargs = build_unsubscribe_feed_kwargs(subscription)
            symbol = subscription.symbol
            logger.info(
                "Calling unsubscribe_feeds with arguments: {kwargs}",
                kwargs=kwargs,
            )
            try:
                result = self._client.unsubscribe_feeds(**kwargs)
                self._raise_if_feed_call_failed(result)
            except Exception as error:
                logger.error(
                    "Unsubscribe failed: {symbol} - {error}\n{traceback}",
                    symbol=symbol,
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
        """Attach SDK quote callback if supported."""
        if hasattr(self._client, "on_ticks"):
            setattr(self._client, "on_ticks", handler)

    @staticmethod
    def _raise_if_feed_call_failed(result: Any) -> None:
        """Raise when Breeze SDK returns an error string instead of a dict."""
        if isinstance(result, str):
            raise RuntimeError(result)
