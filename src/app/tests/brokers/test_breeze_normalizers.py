"""Breeze normalizer and utility tests."""

from decimal import Decimal

import pytest

from app.brokers.breeze.normalizers.historical_normalizer import \
    normalize_historical
from app.brokers.breeze.normalizers.option_chain_normalizer import \
    normalize_option_chain
from app.brokers.breeze.normalizers.order_normalizer import normalize_order
from app.brokers.breeze.normalizers.portfolio_normalizer import (
    normalize_funds, normalize_profile)
from app.brokers.breeze.normalizers.quote_normalizer import normalize_quote
from app.brokers.breeze.utilities import (map_historical_interval,
                                          map_order_type, to_decimal)
from app.brokers.shared.enums import HistoricalInterval, OrderType
from app.brokers.shared.exceptions import BrokerNotSupportedException


def test_quote_normalizer() -> None:
    """Quote normalizer should map Breeze fields."""
    quote = normalize_quote(
        "NIFTY",
        "NFO",
        [{"ltp": "24500", "open": "24400", "high": "24600", "low": "24350"}],
    )
    assert quote.ltp == Decimal("24500")


def test_order_normalizer() -> None:
    """Order normalizer should map order fields."""
    order = normalize_order(
        {
            "order_id": "1",
            "exchange_code": "NFO",
            "stock_code": "NIFTY",
            "product_type": "futures",
            "action": "buy",
            "order_type": "limit",
            "quantity": "25",
            "status": "Executed",
        }
    )
    assert order.order_id == "1"


def test_portfolio_normalizer() -> None:
    """Portfolio normalizer should map profile and funds."""
    profile = normalize_profile(
        "BREEZE",
        {"Success": {"idirect_user_name": "John", "idirect_userid": "1"}},
    )
    assert profile.user_name == "John"
    funds = normalize_funds({"Success": {"total_bank_balance": "50000"}})
    assert funds.available_cash == Decimal("50000")


def test_option_chain_normalizer() -> None:
    """Option chain normalizer should build rows."""
    chain = normalize_option_chain(
        "NIFTY",
        "NFO",
        "30-Jan-2026",
        [{"strike_price": "24500", "right": "call", "ltp": "100"}],
        atm_strike=Decimal("24500"),
    )
    assert chain.rows[0].is_atm is True


def test_historical_normalizer() -> None:
    """Historical normalizer should parse bars."""
    bars = normalize_historical(
        [
            {
                "datetime": "01-Jan-2026 09:15:00",
                "open": "1",
                "high": "2",
                "low": "1",
                "close": "2",
            }
        ]
    )
    assert bars[0].close == Decimal("2")


def test_utility_mappings() -> None:
    """Utility mappings should convert enums."""
    assert map_order_type(OrderType.MARKET) == ("market", "")
    assert map_historical_interval(HistoricalInterval.ONE_MINUTE) == "1minute"
    assert to_decimal("10.5") == Decimal("10.5")
    with pytest.raises(BrokerNotSupportedException):
        map_historical_interval(HistoricalInterval.FIFTEEN_MINUTE)
