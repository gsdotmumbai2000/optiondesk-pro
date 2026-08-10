"""Build Breeze subscribe_feeds / unsubscribe_feeds argument maps."""

from typing import Any

from app.brokers.shared.enums import ProductType
from app.brokers.shared.models import QuoteSubscription

_INDEX_SYMBOLS = frozenset({"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"})
_SPOT_EXCHANGES = frozenset({"nse", "bse"})

# Breeze's NSE cash-segment scrip dictionary (stock_script_dict_list[1]) stores
# these indices under legacy short codes rather than the application's
# canonical symbol. Confirmed against the live NSEScripMaster.txt security
# master. This mapping applies only to NSE lookups: NFO/BFO contract names are
# built from the canonical index name as the underlying and must not be
# rewritten.
_NSE_INDEX_STOCK_CODE_MAP: dict[str, str] = {
    "NIFTY": "NIFTY",
    "BANKNIFTY": "CNXBAN",
    "FINNIFTY": "NIFFIN",
    "MIDCPNIFTY": "NIFSEL",
}


def resolve_breeze_stock_code(symbol: str, exchange_code: str) -> str:
    """Map a canonical symbol to Breeze's NSE scrip-master stock_code, if applicable."""
    if exchange_code != "nse":
        return symbol
    return _NSE_INDEX_STOCK_CODE_MAP.get(symbol.strip().upper(), symbol)


def _clean_str(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _is_index_spot(subscription: QuoteSubscription) -> bool:
    symbol = subscription.symbol.strip().upper()
    exchange = subscription.exchange.strip().lower()
    return (
        symbol in _INDEX_SYMBOLS
        and exchange in _SPOT_EXCHANGES
        and subscription.product_type == ProductType.CASH
    )


def _is_spot_subscription(subscription: QuoteSubscription) -> bool:
    exchange = subscription.exchange.strip().lower()
    return (
        subscription.product_type == ProductType.CASH
        and exchange in _SPOT_EXCHANGES
    )


def build_subscribe_feed_kwargs(subscription: QuoteSubscription) -> dict[str, Any]:
    """Build keyword arguments for Breeze subscribe_feeds."""
    exchange = subscription.exchange.strip().lower()
    symbol = subscription.symbol.strip()
    product_type = subscription.product_type

    kwargs: dict[str, Any] = {
        "exchange_code": exchange,
        "stock_code": resolve_breeze_stock_code(symbol, exchange),
        "get_exchange_quotes": True,
        "get_market_depth": subscription.mode.value == "DEPTH",
    }

    if product_type == ProductType.OPTIONS:
        kwargs["product_type"] = "options"
        expiry = _clean_str(subscription.expiry_date)
        if expiry is not None:
            kwargs["expiry_date"] = expiry
        strike = _clean_str(subscription.strike_price)
        if strike is not None:
            kwargs["strike_price"] = strike
        right = _clean_str(subscription.option_right)
        if right is not None:
            kwargs["right"] = right.lower()
    elif product_type in (ProductType.FUTURES, ProductType.CURRENCY, ProductType.COMMODITY):
        kwargs["product_type"] = "futures"
        expiry = _clean_str(subscription.expiry_date)
        if expiry is not None:
            kwargs["expiry_date"] = expiry
    elif _is_index_spot(subscription) or _is_spot_subscription(subscription):
        kwargs["product_type"] = "cash"
    else:
        kwargs["product_type"] = product_type.value.lower()

    interval = _clean_str(subscription.interval)
    if interval is not None:
        kwargs["interval"] = interval

    return kwargs


def build_unsubscribe_feed_kwargs(subscription: QuoteSubscription) -> dict[str, Any]:
    """Build keyword arguments for Breeze unsubscribe_feeds."""
    return build_subscribe_feed_kwargs(subscription)
