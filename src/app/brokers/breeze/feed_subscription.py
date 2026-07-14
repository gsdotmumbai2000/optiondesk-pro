"""Build Breeze subscribe_feeds / unsubscribe_feeds argument maps."""

from typing import Any

from app.brokers.shared.enums import ProductType
from app.brokers.shared.models import QuoteSubscription

_DERIVATIVE_EXCHANGES = frozenset({"nfo", "ndx", "mcx", "bfo"})


def _clean_str(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def build_subscribe_feed_kwargs(subscription: QuoteSubscription) -> dict[str, Any]:
    """Build keyword arguments for Breeze subscribe_feeds."""
    exchange = subscription.exchange.strip().lower()
    product_type = subscription.product_type.value.lower()

    kwargs: dict[str, Any] = {
        "exchange_code": exchange,
        "stock_code": subscription.symbol.strip(),
        "product_type": product_type,
        "get_exchange_quotes": True,
        "get_market_depth": subscription.mode.value == "DEPTH",
    }

    needs_derivative_fields = exchange in _DERIVATIVE_EXCHANGES or subscription.product_type in (
        ProductType.FUTURES,
        ProductType.OPTIONS,
        ProductType.CURRENCY,
        ProductType.COMMODITY,
    )
    if needs_derivative_fields:
        expiry = _clean_str(subscription.expiry_date)
        if expiry is not None:
            kwargs["expiry_date"] = expiry

        if subscription.product_type == ProductType.OPTIONS:
            strike = _clean_str(subscription.strike_price)
            if strike is not None:
                kwargs["strike_price"] = strike
            right = _clean_str(subscription.option_right)
            if right is not None:
                kwargs["right"] = right.lower()

    interval = _clean_str(subscription.interval)
    if interval is not None:
        kwargs["interval"] = interval

    return kwargs


def build_unsubscribe_feed_kwargs(subscription: QuoteSubscription) -> dict[str, Any]:
    """Build keyword arguments for Breeze unsubscribe_feeds."""
    return build_subscribe_feed_kwargs(subscription)
