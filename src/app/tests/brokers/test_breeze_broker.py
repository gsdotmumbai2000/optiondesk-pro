"""Breeze broker tests."""

from datetime import datetime
from decimal import Decimal

import pytest

from app.brokers.bootstrap import BrokerProvider
from app.brokers.shared.enums import (HistoricalInterval, OrderSide, OrderType,
                                      ProductType)
from app.brokers.shared.exceptions import BrokerConnectionException
from app.brokers.shared.models import (HistoricalRequest, OptionChainRequest,
                                       OrderModification, OrderRequest,
                                       QuoteSubscription)


def test_connect_and_authenticate(broker_provider: BrokerProvider) -> None:
    """Broker should connect and authenticate."""
    broker_provider.manager.connect()
    assert broker_provider.broker_service.is_connected()
    assert broker_provider.broker_service.health().is_session_valid


def test_get_profile_and_portfolio(broker_provider: BrokerProvider) -> None:
    """Broker should return normalized profile and portfolio."""
    broker_provider.manager.connect()
    profile = broker_provider.broker_service.get_profile()
    assert profile.user_name == "Test User"
    funds = broker_provider.broker_service.get_funds()
    assert funds.available_cash == Decimal("100000")
    holdings = broker_provider.broker_service.get_holdings()
    assert holdings[0].symbol == "INFY"
    positions = broker_provider.broker_service.get_positions()
    assert positions[0].symbol == "NIFTY"


def test_trading_flow(broker_provider: BrokerProvider) -> None:
    """Broker should place, modify, and cancel orders."""
    broker_provider.manager.connect()
    request = OrderRequest(
        symbol="NIFTY",
        exchange="NFO",
        product_type=ProductType.FUTURES,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=25,
        price=Decimal("24500"),
    )
    placed = broker_provider.broker_service.place_order(request)
    assert placed.order_id == "ORD2"
    modified = broker_provider.broker_service.modify_order(
        OrderModification(order_id="ORD2", exchange="NFO", quantity=50)
    )
    assert modified.quantity == 50
    cancelled = broker_provider.broker_service.cancel_order("NFO", "ORD2")
    assert cancelled.status == "Cancelled"


def test_market_data_and_chain(broker_provider: BrokerProvider) -> None:
    """Broker should return quotes and option chain."""
    broker_provider.manager.connect()
    quote = broker_provider.broker_service.get_quotes("NIFTY", "NFO")
    assert quote.ltp == Decimal("24500")
    chain = broker_provider.broker_service.get_option_chain(
        OptionChainRequest(
            underlying="NIFTY", exchange="NFO", expiry_date="30-Jan-2026"
        )
    )
    assert chain.rows[0].strike_price == Decimal("24500")


def test_historical_and_instrument_master(broker_provider: BrokerProvider) -> None:
    """Broker should return historical bars and instrument master."""
    broker_provider.manager.connect()
    bars = broker_provider.broker_service.get_historical_data(
        HistoricalRequest(
            symbol="NIFTY",
            exchange="NFO",
            product_type=ProductType.FUTURES,
            interval=HistoricalInterval.ONE_MINUTE,
            from_date=datetime(2026, 1, 1, 9, 15),
            to_date=datetime(2026, 1, 1, 15, 30),
        )
    )
    assert bars[0].close == Decimal("24480")
    master = broker_provider.broker_service.download_instrument_master()
    assert master[0]["stock_code"] == "NIFTY"


def test_subscriptions(broker_provider: BrokerProvider) -> None:
    """Broker should subscribe and unsubscribe quotes."""
    broker_provider.manager.connect()
    subscription = QuoteSubscription(symbol="NIFTY", exchange="NFO")
    broker_provider.broker_service.subscribe_quotes(subscription)
    broker_provider.broker_service.unsubscribe_quotes(subscription)


def test_session_required_without_auth(broker_provider: BrokerProvider) -> None:
    """API calls should fail when session is invalid."""
    with pytest.raises(BrokerConnectionException):
        broker_provider.broker_service.get_funds()
