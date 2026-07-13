"""Subscription validation."""

from app.market_data.exceptions import MarketDataSubscriptionException


class SubscriptionValidator:
    """Validate subscription requests."""

    def validate(self, symbol: str, exchange: str) -> None:
        """Validate symbol and exchange."""
        if not symbol.strip():
            raise MarketDataSubscriptionException("Symbol is required")
        if not exchange.strip():
            raise MarketDataSubscriptionException("Exchange is required")
