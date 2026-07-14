"""Tests for Breeze websocket subscription layer."""

from typing import Any

import pytest

from app.brokers.breeze.websocket import BreezeWebSocket
from app.brokers.shared.enums import ProductType
from app.brokers.shared.models import QuoteSubscription


class _RecordingClient:
    def __init__(self) -> None:
        self.subscribe_calls: list[dict[str, Any]] = []
        self.unsubscribe_calls: list[dict[str, Any]] = []
        self.subscribe_result: Any = {"message": "subscribed"}
        self.unsubscribe_result: Any = {"message": "unsubscribed"}

    def subscribe_feeds(self, **kwargs: Any) -> Any:
        self.subscribe_calls.append(kwargs)
        return self.subscribe_result

    def unsubscribe_feeds(self, **kwargs: Any) -> Any:
        self.unsubscribe_calls.append(kwargs)
        return self.unsubscribe_result

    def ws_connect(self) -> None:
        return None

    def ws_disconnect(self) -> None:
        return None


def test_subscribe_quotes_passes_clean_equity_kwargs() -> None:
    """Equity subscriptions should call subscribe_feeds without derivative fields."""
    client = _RecordingClient()
    websocket = BreezeWebSocket(client)
    subscription = QuoteSubscription(symbol="NIFTY", exchange="NSE", product_type=ProductType.CASH)

    websocket.subscribe_quotes(subscription)

    assert len(client.subscribe_calls) == 1
    assert client.subscribe_calls[0] == {
        "exchange_code": "nse",
        "stock_code": "NIFTY",
        "product_type": "cash",
        "get_exchange_quotes": True,
        "get_market_depth": False,
    }
    assert subscription in websocket._quote_subscriptions


def test_subscribe_quotes_raises_on_sdk_error_string() -> None:
    """SDK error strings should be treated as subscription failures."""
    client = _RecordingClient()
    client.subscribe_result = "Exception while subscribing to feeds cannot unpack non-iterable NoneType object"
    websocket = BreezeWebSocket(client)
    subscription = QuoteSubscription(symbol="NIFTY", exchange="NSE")

    with pytest.raises(RuntimeError, match="cannot unpack"):
        websocket.subscribe_quotes(subscription)

    assert websocket._quote_subscriptions == []


def test_resubscribe_does_not_duplicate_tracked_subscriptions() -> None:
    """Resubscribe should not append duplicate subscription entries."""
    client = _RecordingClient()
    websocket = BreezeWebSocket(client)
    subscription = QuoteSubscription(symbol="NIFTY", exchange="NSE")

    websocket.subscribe_quotes(subscription)
    websocket.resubscribe_all()

    assert len(client.subscribe_calls) == 2
    assert len(websocket._quote_subscriptions) == 1
