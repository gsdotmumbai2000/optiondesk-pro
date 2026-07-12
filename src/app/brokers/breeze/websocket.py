"""Breeze websocket manager."""

from threading import RLock
from typing import Any, Callable

from app.brokers.breeze.client_port import BreezeClientPort
from app.brokers.breeze.normalizers.quote_normalizer import normalize_quote
from app.brokers.events import OptionChainUpdatedEvent, QuoteUpdatedEvent
from app.brokers.shared.models import OptionChainRequest, QuoteSubscription
from app.events.event_bus import EventBus


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
            self._client.subscribe_feeds(
                exchange_code=subscription.exchange.lower(),
                stock_code=subscription.symbol,
                product_type=subscription.product_type.value.lower(),
                expiry_date=subscription.expiry_date,
                strike_price=subscription.strike_price,
                right=subscription.option_right.lower(),
                interval=subscription.interval,
                get_exchange_quotes=True,
                get_market_depth=subscription.mode.value == "DEPTH",
            )
            self._quote_subscriptions.append(subscription)

    def unsubscribe_quotes(self, subscription: QuoteSubscription) -> None:
        """Unsubscribe from quote feed."""
        with self._lock:
            self._client.unsubscribe_feeds(
                exchange_code=subscription.exchange.lower(),
                stock_code=subscription.symbol,
                product_type=subscription.product_type.value.lower(),
                expiry_date=subscription.expiry_date,
                strike_price=subscription.strike_price,
                right=subscription.option_right.lower(),
                interval=subscription.interval,
            )
            self._quote_subscriptions = [
                item
                for item in self._quote_subscriptions
                if item.symbol != subscription.symbol
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
