"""Extended normalizer and manager tests."""

from unittest.mock import MagicMock

import pytest

from app.brokers.bootstrap import BrokerProvider
from app.brokers.breeze.authentication import BreezeAuthentication
from app.brokers.breeze.normalizers.order_normalizer import normalize_order
from app.brokers.breeze.normalizers.quote_normalizer import normalize_quote
from app.brokers.breeze.utilities import (map_order_side, map_order_type,
                                          map_product_type, map_validity,
                                          to_int, unwrap_success)
from app.brokers.broker_factory.factory import BrokerFactory
from app.brokers.broker_manager.manager import BrokerManager
from app.brokers.dhan.broker import DhanBroker
from app.brokers.shared.enums import (OrderSide, OrderType, OrderValidity,
                                      ProductType)
from app.brokers.shared.exceptions import (BrokerException,
                                           BrokerSessionExpiredException)
from app.brokers.shared.models import OptionChainRequest
from app.brokers.zerodha.broker import ZerodhaBroker
from app.config.models.app_config import BrokerConfig
from app.events.event_bus import EventBus
from app.security.credential_manager import CredentialManager
from app.tests.brokers.conftest import MockBreezeClient


def test_quote_depth_normalizer() -> None:
    """Quote normalizer should parse depth levels."""
    quote = normalize_quote(
        "NIFTY",
        "NFO",
        {
            "ltp": "100",
            "bids": [{"price": "99", "quantity": "10", "orders": "2"}],
            "offers": [{"price": "101", "quantity": "5", "orders": "1"}],
        },
    )
    assert len(quote.bid_depth) == 1
    assert len(quote.ask_depth) == 1


def test_order_normalizer_variants() -> None:
    """Order normalizer should handle multiple order types."""
    market = normalize_order(
        {
            "order_id": "1",
            "exchange_code": "NSE",
            "stock_code": "INFY",
            "product_type": "options",
            "action": "sell",
            "order_type": "market",
            "quantity": "1",
            "validity": "ioc",
            "status": "Queued",
        }
    )
    assert market.order_type.value == "MARKET"
    assert market.validity.value == "IOC"


def test_utility_mappings_extended() -> None:
    """Utility helpers should map all supported values."""
    assert map_product_type(ProductType.OPTIONS) == "options"
    assert map_order_side(OrderSide.SELL) == "sell"
    assert map_validity(OrderValidity.GTC) == "vtc"
    assert map_order_type(OrderType.STOP_LOSS) == ("stoploss", "Y")
    assert to_int("12.5") == 12
    with pytest.raises(BrokerException):
        unwrap_success({"Error": "failed"})


def test_manager_reconnect_and_refresh(broker_provider: BrokerProvider) -> None:
    """Manager should reconnect and refresh session."""
    broker_provider.manager.connect()
    broker_provider.manager.reconnect()
    broker_provider.manager.refresh_session()
    assert broker_provider.manager.health().is_session_valid


def test_manager_session_expired_on_refresh_failure(
    broker_config: BrokerConfig,
    credential_manager: CredentialManager,
) -> None:
    """Refresh should surface session expiry."""
    client = MockBreezeClient("key")

    def bad_details(api_session: str = "") -> dict[str, object]:
        return {"Error": "expired"}

    client.get_customer_details = bad_details  # type: ignore[method-assign]
    factory = BrokerFactory(
        broker_config,
        credential_manager,
        EventBus(),
        client_factory=lambda key: client,
    )
    manager = BrokerManager(factory, broker_config, EventBus())
    manager.connect()
    with pytest.raises(BrokerSessionExpiredException):
        manager.refresh_session()


def test_stub_broker_health_only(broker_config: BrokerConfig) -> None:
    """Stub brokers should expose health without connect."""
    zerodha = ZerodhaBroker(broker_config)
    dhan = DhanBroker(broker_config)
    assert zerodha.health().broker_code == "ZERODHA"
    assert dhan.health().broker_code == "DHAN"
    zerodha.disconnect()
    dhan.logout()


def test_authentication_error_response() -> None:
    """Authentication should fail on SDK error response."""
    client = MagicMock()
    client.generate_session.return_value = {"Error": "bad session"}
    manager = CredentialManager()
    manager.store_api_key("A", "k")
    manager.store_api_secret("A", "s")
    manager.store_session_token("A", "t")
    auth = BreezeAuthentication(client, manager, "A")
    with pytest.raises(Exception):
        auth.authenticate()


def test_option_chain_subscription(broker_provider: BrokerProvider) -> None:
    """Broker should manage option chain subscriptions."""
    broker_provider.manager.connect()
    request = OptionChainRequest(
        underlying="NIFTY",
        exchange="NFO",
        expiry_date="30-Jan-2026",
    )
    broker_provider.broker_service.subscribe_option_chain(request)
    broker_provider.broker_service.unsubscribe_option_chain(request)
