"""Instrument service tests."""

from datetime import date
from decimal import Decimal

import pytest

from app.market.bootstrap import MarketMasterProvider
from app.market.enums import ExchangeCode, InstrumentType


def test_default_underlyings_loaded(market_provider: MarketMasterProvider) -> None:
    """Default index underlyings should be available."""
    service = market_provider.instrument_service
    nifty = service.find_by_symbol("NIFTY")
    assert len(nifty) == 1
    assert nifty[0].exchange == ExchangeCode.NSEFO


def test_find_by_exchange(market_provider: MarketMasterProvider) -> None:
    """Exchange search should return NSEFO instruments."""
    results = market_provider.instrument_service.find_by_exchange("NSEFO")
    assert len(results) >= 4


def test_find_by_instrument_type(market_provider: MarketMasterProvider) -> None:
    """Type search should return index instruments."""
    results = market_provider.instrument_service.find_by_instrument_type(
        InstrumentType.INDEX
    )
    assert all(item.instrument_type == InstrumentType.INDEX for item in results)


def test_lot_size_and_tick_size(market_provider: MarketMasterProvider) -> None:
    """Utility accessors should return specification values."""
    service = market_provider.instrument_service
    assert service.get_lot_size("NIFTY") == 25
    assert service.get_tick_size("BANKNIFTY") == Decimal("0.05")
    assert service.get_strike_interval("NIFTY") == Decimal("50")
    assert service.get_freeze_quantity("NIFTY") == 1800


def test_strike_helpers(market_provider: MarketMasterProvider) -> None:
    """Strike helpers should round to valid intervals."""
    service = market_provider.instrument_service
    assert service.atm_strike("NIFTY", Decimal("24523")) == Decimal("24500")
    assert service.nearest_strike("NIFTY", Decimal("24540")) == Decimal("24550")


def test_nearest_weekly_expiry(market_provider: MarketMasterProvider) -> None:
    """Nearest weekly expiry should be on configured weekday."""
    service = market_provider.instrument_service
    expiry = service.weekly_expiry("NIFTY", "NSEFO", on_date=date(2026, 7, 6))
    assert expiry is not None
    assert expiry.expiry_date.weekday() == 1


def test_unknown_underlying_raises(market_provider: MarketMasterProvider) -> None:
    """Unknown underlying should raise LookupError."""
    with pytest.raises(LookupError):
        market_provider.instrument_service.get_lot_size("UNKNOWN")
