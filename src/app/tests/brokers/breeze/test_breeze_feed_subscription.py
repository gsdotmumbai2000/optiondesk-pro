"""Tests for Breeze feed subscription argument builder."""

import pytest

from app.brokers.breeze.feed_subscription import (
    build_subscribe_feed_kwargs,
    build_unsubscribe_feed_kwargs,
    resolve_breeze_stock_code,
)
from app.brokers.shared.enums import ProductType, QuoteSubscriptionMode
from app.brokers.shared.models import QuoteSubscription


def test_equity_spot_omits_option_fields() -> None:
    """NSE cash subscriptions should not include derivative-only fields."""
    subscription = QuoteSubscription(symbol="NIFTY", exchange="NSE", product_type=ProductType.CASH)
    kwargs = build_subscribe_feed_kwargs(subscription)
    assert kwargs == {
        "exchange_code": "nse",
        "stock_code": "NIFTY",
        "product_type": "cash",
        "get_exchange_quotes": True,
        "get_market_depth": False,
    }
    assert "expiry_date" not in kwargs
    assert "strike_price" not in kwargs
    assert "right" not in kwargs
    assert "interval" not in kwargs


def test_index_spot_depth_mode() -> None:
    """Depth mode should set get_market_depth without option fields."""
    subscription = QuoteSubscription(
        symbol="BANKNIFTY",
        exchange="NSE",
        product_type=ProductType.CASH,
        mode=QuoteSubscriptionMode.DEPTH,
    )
    kwargs = build_subscribe_feed_kwargs(subscription)
    assert kwargs["get_market_depth"] is True
    assert "expiry_date" not in kwargs


def test_nfo_options_includes_derivative_fields() -> None:
    """NFO option subscriptions should include expiry, strike, and right."""
    subscription = QuoteSubscription(
        symbol="NIFTY",
        exchange="NFO",
        product_type=ProductType.OPTIONS,
        expiry_date="30-Jun-2026",
        strike_price="24000",
        option_right="CALL",
    )
    kwargs = build_subscribe_feed_kwargs(subscription)
    assert kwargs["exchange_code"] == "nfo"
    assert kwargs["product_type"] == "options"
    assert kwargs["expiry_date"] == "30-Jun-2026"
    assert kwargs["strike_price"] == "24000"
    assert kwargs["right"] == "call"


def test_nfo_futures_omits_strike_and_right() -> None:
    """NFO futures should include expiry but not option-specific fields."""
    subscription = QuoteSubscription(
        symbol="NIFTY",
        exchange="NFO",
        product_type=ProductType.FUTURES,
        expiry_date="30-Jun-2026",
    )
    kwargs = build_subscribe_feed_kwargs(subscription)
    assert kwargs["expiry_date"] == "30-Jun-2026"
    assert "strike_price" not in kwargs
    assert "right" not in kwargs


def test_omits_empty_optional_values() -> None:
    """Empty strings should be omitted rather than passed to the SDK."""
    subscription = QuoteSubscription(
        symbol="NIFTY",
        exchange="NSE",
        product_type=ProductType.CASH,
        expiry_date="",
        strike_price="",
        option_right="",
        interval="",
    )
    kwargs = build_subscribe_feed_kwargs(subscription)
    assert "expiry_date" not in kwargs
    assert "strike_price" not in kwargs
    assert "right" not in kwargs
    assert "interval" not in kwargs


def test_interval_included_when_set() -> None:
    """OHLCV interval should be passed only when provided."""
    subscription = QuoteSubscription(
        symbol="NIFTY",
        exchange="NSE",
        product_type=ProductType.CASH,
        interval="1minute",
    )
    kwargs = build_subscribe_feed_kwargs(subscription)
    assert kwargs["interval"] == "1minute"


def test_unsubscribe_matches_subscribe() -> None:
    """Unsubscribe kwargs should mirror subscribe identity fields."""
    subscription = QuoteSubscription(symbol="RELIANCE", exchange="NSE")
    assert build_unsubscribe_feed_kwargs(subscription) == build_subscribe_feed_kwargs(subscription)


def test_all_index_symbols_omit_derivative_fields() -> None:
    """Default index symbols should never include derivative-only fields."""
    for symbol in ("NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"):
        subscription = QuoteSubscription(symbol=symbol, exchange="NSE", product_type=ProductType.CASH)
        kwargs = build_subscribe_feed_kwargs(subscription)
        assert kwargs["product_type"] == "cash"
        assert "expiry_date" not in kwargs
        assert "strike_price" not in kwargs
        assert "right" not in kwargs


@pytest.mark.parametrize(
    ("symbol", "breeze_stock_code"),
    [
        ("NIFTY", "NIFTY"),
        ("BANKNIFTY", "CNXBAN"),
        ("FINNIFTY", "NIFFIN"),
        ("MIDCPNIFTY", "NIFSEL"),
    ],
)
def test_nse_index_stock_code_is_mapped_to_breeze_scrip_code(
    symbol: str, breeze_stock_code: str
) -> None:
    """NSE cash-segment subscribe_feeds calls must use Breeze's own scrip-master
    codes for these indices; Breeze's NSE dictionary does not contain
    "BANKNIFTY"/"FINNIFTY"/"MIDCPNIFTY" as literal keys (confirmed against the
    live NSEScripMaster.txt security master)."""
    subscription = QuoteSubscription(symbol=symbol, exchange="NSE", product_type=ProductType.CASH)
    kwargs = build_subscribe_feed_kwargs(subscription)
    assert kwargs["stock_code"] == breeze_stock_code


def test_nse_index_stock_code_mapping_applies_to_unsubscribe_too() -> None:
    """Subscribe and unsubscribe must use the same Breeze broker identifier."""
    subscription = QuoteSubscription(symbol="BANKNIFTY", exchange="NSE", product_type=ProductType.CASH)
    subscribe_kwargs = build_subscribe_feed_kwargs(subscription)
    unsubscribe_kwargs = build_unsubscribe_feed_kwargs(subscription)
    assert subscribe_kwargs["stock_code"] == "CNXBAN"
    assert unsubscribe_kwargs["stock_code"] == "CNXBAN"


def test_index_stock_code_mapping_does_not_apply_outside_nse() -> None:
    """NFO contract names use the canonical index name as their underlying;
    the NSE cash-segment scrip-code mapping must not rewrite it."""
    subscription = QuoteSubscription(
        symbol="BANKNIFTY",
        exchange="NFO",
        product_type=ProductType.OPTIONS,
        expiry_date="30-Jun-2026",
        strike_price="50000",
        option_right="CALL",
    )
    kwargs = build_subscribe_feed_kwargs(subscription)
    assert kwargs["stock_code"] == "BANKNIFTY"


def test_resolve_breeze_stock_code_is_case_insensitive_and_leaves_unknown_symbols() -> None:
    """The resolver should only rewrite known NSE index aliases."""
    assert resolve_breeze_stock_code("banknifty", "nse") == "CNXBAN"
    assert resolve_breeze_stock_code("RELIANCE", "nse") == "RELIANCE"
    assert resolve_breeze_stock_code("BANKNIFTY", "bse") == "BANKNIFTY"
