"""Subscription domain models."""

from app.brokers.shared.enums import ProductType
from app.brokers.shared.models import QuoteSubscription


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
