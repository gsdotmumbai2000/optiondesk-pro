"""Manage live market data subscriptions."""

from collections.abc import Callable

from app.brokers.broker_interface.interface import BrokerInterface
from app.brokers.shared.enums import ProductType
from app.brokers.shared.models import QuoteSubscription
from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger
from app.market_data.events import SubscriptionAddedEvent, SubscriptionRemovedEvent

logger = get_logger(__name__)

DEFAULT_INDICES: tuple[tuple[str, str, ProductType], ...] = (
    ("NIFTY", "NSE", ProductType.CASH),
    ("BANKNIFTY", "NSE", ProductType.CASH),
    ("FINNIFTY", "NSE", ProductType.CASH),
    ("MIDCPNIFTY", "NSE", ProductType.CASH),
)


class SubscriptionKey:
    """Canonical subscription identity."""

    __slots__ = (
        "symbol",
        "exchange",
        "product_type",
        "expiry_date",
        "strike_price",
        "option_right",
    )

    def __init__(
        self,
        symbol: str,
        exchange: str,
        product_type: ProductType = ProductType.CASH,
        expiry_date: str = "",
        strike_price: str = "",
        option_right: str = "",
    ) -> None:
        self.symbol = symbol
        self.exchange = exchange
        self.product_type = product_type
        self.expiry_date = expiry_date
        self.strike_price = strike_price
        self.option_right = option_right

    def to_quote_subscription(self) -> QuoteSubscription:
        """Convert to broker subscription model."""
        return QuoteSubscription(
            symbol=self.symbol,
            exchange=self.exchange,
            product_type=self.product_type,
            expiry_date=self.expiry_date,
            strike_price=self.strike_price,
            option_right=self.option_right,
        )


class MarketDataSubscriptionManager:
    """Track pending watchlist and active broker subscriptions."""

    def __init__(
        self,
        broker: BrokerInterface,
        event_bus: EventBus | None = None,
        *,
        can_subscribe: Callable[[], bool] | None = None,
    ) -> None:
        """Initialize subscription manager."""
        self._broker = broker
        self._event_bus = event_bus
        self._can_subscribe = can_subscribe or (lambda: False)
        self._pending: dict[str, SubscriptionKey] = {}
        self._active: dict[str, SubscriptionKey] = {}

    def register(
        self,
        symbol: str,
        exchange: str,
        *,
        product_type: ProductType = ProductType.CASH,
        expiry_date: str = "",
        strike_price: str = "",
        option_right: str = "",
    ) -> None:
        """Queue symbol for subscription without contacting broker."""
        key = self._key(symbol, exchange, product_type, expiry_date, strike_price)
        self._pending[key] = SubscriptionKey(
            symbol=symbol,
            exchange=exchange,
            product_type=product_type,
            expiry_date=expiry_date,
            strike_price=strike_price,
            option_right=option_right,
        )
        if self._can_subscribe():
            self._activate_key(key)

    def register_defaults(self) -> None:
        """Register default index symbols as pending."""
        for symbol, exchange, product_type in DEFAULT_INDICES:
            self.register(symbol, exchange, product_type=product_type)

    def activate_pending(self) -> None:
        """Subscribe all pending symbols to broker."""
        for key in list(self._pending):
            self._activate_key(key)
        logger.info(
            "Activated {count} pending market subscriptions",
            count=len(self._active),
        )

    def deactivate_all(self) -> None:
        """Unsubscribe broker feeds while keeping pending watchlist."""
        for sub in list(self._active.values()):
            self._safe_unsubscribe(sub)
            self._publish_removed(sub)
        self._active.clear()
        logger.info("Deactivated market subscriptions, watchlist retained")

    def remove(
        self,
        symbol: str,
        exchange: str,
        *,
        product_type: ProductType = ProductType.CASH,
        expiry_date: str = "",
        strike_price: str = "",
    ) -> None:
        """Remove symbol from watchlist and active subscriptions."""
        key = self._key(symbol, exchange, product_type, expiry_date, strike_price)
        self._pending.pop(key, None)
        active = self._active.pop(key, None)
        if active is not None:
            self._safe_unsubscribe(active)
            self._publish_removed(active)

    def pending_count(self) -> int:
        """Return pending watchlist size."""
        return len(self._pending)

    def active_count(self) -> int:
        """Return active broker subscription count."""
        return len(self._active)

    def _activate_key(self, key: str) -> None:
        if key in self._active or key not in self._pending:
            return
        sub = self._pending[key]
        self._broker.subscribe_quotes(sub.to_quote_subscription())
        self._active[key] = sub
        logger.info(
            "Subscription added: {symbol}@{exchange}",
            symbol=sub.symbol,
            exchange=sub.exchange,
        )
        self._publish_added(sub)

    def _safe_unsubscribe(self, sub: SubscriptionKey) -> None:
        try:
            self._broker.unsubscribe_quotes(sub.to_quote_subscription())
        except Exception as error:
            logger.warning(
                "Unsubscribe failed for {symbol}: {error}",
                symbol=sub.symbol,
                error=error,
            )

    def _key(
        self,
        symbol: str,
        exchange: str,
        product_type: ProductType,
        expiry_date: str,
        strike_price: str,
    ) -> str:
        return f"{exchange}:{symbol}:{product_type.value}:{expiry_date}:{strike_price}"

    def _publish_added(self, sub: SubscriptionKey) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            SubscriptionAddedEvent(
                payload={
                    "symbol": sub.symbol,
                    "exchange": sub.exchange,
                    "product_type": sub.product_type.value,
                }
            )
        )

    def _publish_removed(self, sub: SubscriptionKey) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            SubscriptionRemovedEvent(
                payload={
                    "symbol": sub.symbol,
                    "exchange": sub.exchange,
                    "product_type": sub.product_type.value,
                }
            )
        )
