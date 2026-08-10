"""Tests for Breeze websocket subscription layer."""

from typing import Any

import pytest
from loguru import logger as loguru_logger

from app.brokers.breeze.websocket import BreezeWebSocket
from app.brokers.shared.enums import ProductType
from app.brokers.shared.models import QuoteSubscription


@pytest.fixture
def captured_logs():
    """Capture Loguru output emitted during the test, independent of stdout."""
    messages: list[str] = []
    sink_id = loguru_logger.add(lambda message: messages.append(str(message)), level="DEBUG")
    yield messages
    loguru_logger.remove(sink_id)


class _RecordingClient:
    def __init__(self) -> None:
        self.subscribe_calls: list[dict[str, Any]] = []
        self.unsubscribe_calls: list[dict[str, Any]] = []
        self.ws_connect_calls = 0
        self.subscribe_result: Any = {"message": "subscribed"}
        self.unsubscribe_result: Any = {"message": "unsubscribed"}
        self.on_ticks: Any = None

    def subscribe_feeds(self, **kwargs: Any) -> Any:
        self.subscribe_calls.append(kwargs)
        return self.subscribe_result

    def unsubscribe_feeds(self, **kwargs: Any) -> Any:
        self.unsubscribe_calls.append(kwargs)
        return self.unsubscribe_result

    def ws_connect(self) -> None:
        self.ws_connect_calls += 1

    def ws_disconnect(self) -> None:
        return None


def test_subscribe_quotes_passes_clean_equity_kwargs() -> None:
    """Equity subscriptions should call subscribe_feeds without derivative fields."""
    client = _RecordingClient()
    websocket = BreezeWebSocket(client)
    websocket.set_quote_handler(lambda _payload: None)
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


def test_sdk_callback_wrapper_is_registered() -> None:
    """BreezeConnect.on_ticks should point to the SDK entry wrapper."""
    client = _RecordingClient()
    websocket = BreezeWebSocket(client)
    received: list[Any] = []
    websocket.set_quote_handler(received.append)

    assert client.on_ticks is websocket._on_sdk_ticks
    client.on_ticks({"stock_code": "NIFTY"})
    assert received == [{"stock_code": "NIFTY"}]


def test_subscribe_quotes_raises_on_sdk_error_string() -> None:
    """SDK error strings should be treated as subscription failures."""
    client = _RecordingClient()
    client.subscribe_result = "Exception while subscribing to feeds cannot unpack non-iterable NoneType object"
    websocket = BreezeWebSocket(client)
    websocket.set_quote_handler(lambda _payload: None)
    subscription = QuoteSubscription(symbol="NIFTY", exchange="NSE")

    with pytest.raises(RuntimeError, match="cannot unpack"):
        websocket.subscribe_quotes(subscription)

    assert websocket._quote_subscriptions == []


def test_subscribe_quotes_raises_on_invalid_token_error_string(
    captured_logs: list[str],
) -> None:
    """When Breeze's stock_code lookup fails, its own SDK wraps the resulting
    exception into an error string return (see get_stock_token_value /
    subscribe_feeds in the vendored SDK). The websocket layer must raise
    rather than record the subscription as successful, and must never log
    "Subscription successful" for it."""
    client = _RecordingClient()
    client.subscribe_result = (
        "Exception while subscribing to feeds Breeze returned an invalid "
        "token for stock_code='BANKNIFTY' exchange_code='NSE': stock_code "
        "was not found in Breeze's own scrip dictionary "
        "(tokens=('4.1!False', '4.2!False'))"
    )
    websocket = BreezeWebSocket(client)
    websocket.set_quote_handler(lambda _payload: None)
    subscription = QuoteSubscription(symbol="BANKNIFTY", exchange="NSE", product_type=ProductType.CASH)

    with pytest.raises(RuntimeError, match="invalid token"):
        websocket.subscribe_quotes(subscription)

    assert subscription not in websocket._quote_subscriptions
    log_text = "".join(captured_logs)
    assert "Subscription successful" not in log_text


def test_ws_connect_deferred_until_handler_registered() -> None:
    """ws_connect should not run before set_quote_handler."""
    client = _RecordingClient()
    websocket = BreezeWebSocket(client)

    websocket.connect()
    assert client.ws_connect_calls == 0

    websocket.set_quote_handler(lambda _payload: None)
    assert client.ws_connect_calls == 1


def test_resubscribe_does_not_duplicate_tracked_subscriptions() -> None:
    """Resubscribe should not append duplicate subscription entries."""
    client = _RecordingClient()
    websocket = BreezeWebSocket(client)
    websocket.set_quote_handler(lambda _payload: None)
    subscription = QuoteSubscription(symbol="NIFTY", exchange="NSE")

    websocket.subscribe_quotes(subscription)
    websocket.resubscribe_all()

    assert len(client.subscribe_calls) == 2
    assert len(websocket._quote_subscriptions) == 1
