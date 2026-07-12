"""Manage live market data subscriptions."""

from dataclasses import dataclass

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


@dataclass(frozen=True, slots=True)
class SubscriptionKey:
    """Canonical subscription identity."""

    symbol: str
    exchange: str
    product_type: ProductType
    expiry_date: str = ""
    strike_price: str = ""
    option_right: str = ""

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
    """Track and apply broker quote subscriptions."""

    def __init__(
        self,
        broker: BrokerInterface,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize subscription manager."""
        self._broker = broker
        self._event_bus = event_bus
        self._active: dict[str, SubscriptionKey] = {}

    def subscribe(
        self,
        symbol: str,
        exchange: str,
        *,
        product_type: ProductType = ProductType.CASH,
        expiry_date: str = "",
        strike_price: str = "",
        option_right: str = "",
    ) -> None:
        """Subscribe to live quotes for an instrument."""
        key = self._key(symbol, exchange, product_type, expiry_date, strike_price)
        if key in self._active:
            return
        sub = SubscriptionKey(
            symbol=symbol,
            exchange=exchange,
            product_type=product_type,
            expiry_date=expiry_date,
            strike_price=strike_price,
            option_right=option_right,
        )
        self._broker.subscribe_quotes(sub.to_quote_subscription())
        self._active[key] = sub
        logger.info("Subscription added: {symbol}@{exchange}", symbol=symbol, exchange=exchange)
        self._publish_added(sub)

    def unsubscribe(
        self,
        symbol: str,
        exchange: str,
        *,
        product_type: ProductType = ProductType.CASH,
        expiry_date: str = "",
        strike_price: str = "",
    ) -> None:
        """Unsubscribe from live quotes."""
        key = self._key(symbol, exchange, product_type, expiry_date, strike_price)
        sub = self._active.pop(key, None)
        if sub is None:
            return
        self._broker.unsubscribe_quotes(sub.to_quote_subscription())
        logger.info("Subscription removed: {symbol}@{exchange}", symbol=symbol, exchange=exchange)
        self._publish_removed(sub)

    def subscribe_defaults(self) -> None:
        """Subscribe default index symbols."""
        for symbol, exchange, product_type in DEFAULT_INDICES:
            self.subscribe(symbol, exchange, product_type=product_type)

    def resubscribe_all(self) -> None:
        """Resubscribe all active instruments after reconnect."""
        for sub in list(self._active.values()):
            self._broker.subscribe_quotes(sub.to_quote_subscription())
        logger.info("Resubscribed {count} instruments", count=len(self._active))

    def active_count(self) -> int:
        """Return active subscription count."""
        return len(self._active)

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
