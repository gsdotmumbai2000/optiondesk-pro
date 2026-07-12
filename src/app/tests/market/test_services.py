"""Market service layer tests."""

from datetime import date, datetime, time
from decimal import Decimal

import pytest

from app.market.bootstrap import MarketMasterProvider
from app.market.enums import InstrumentType
from app.market.instrument_master.models import (Instrument,
                                                 InstrumentSpecification)


def test_calendar_service_methods(market_provider: MarketMasterProvider) -> None:
    """Calendar service should expose trading day helpers."""
    service = market_provider.calendar_service
    trading_day = date(2026, 1, 5)
    assert service.is_trading_day("NSEFO", trading_day)
    assert service.market_open("NSEFO") == time(9, 15)
    assert service.market_close("NSEFO") == time(15, 30)
    assert service.pre_open_window("NSEFO") is not None
    assert service.post_close_window("NSEFO") is not None
    moment = datetime(2026, 1, 5, 10, 0)
    assert service.is_market_open("NSEFO", moment)
    assert service.is_half_day("NSEFO", trading_day) is False


def test_expiry_service_methods(market_provider: MarketMasterProvider) -> None:
    """Expiry service should expose expiry calculations."""
    service = market_provider.expiry_service
    on_date = date(2026, 1, 5)
    nearest = service.nearest_expiry("NIFTY", "NSEFO", on_date=on_date)
    assert nearest is not None
    next_exp = service.next_expiry("NIFTY", "NSEFO", after_date=nearest.expiry_date)
    assert next_exp is not None
    assert service.calculate_dte("NSEFO", on_date, nearest.expiry_date) >= 0
    now = datetime(2026, 1, 5, 10, 0)
    assert service.calculate_tte("NSEFO", now, nearest.expiry_date) > 0
    assert service.validate_expiry("NSEFO", nearest.expiry_date) is True


def test_holiday_service_muhurat(market_provider: MarketMasterProvider) -> None:
    """Holiday service should report muhurat sessions when configured."""
    service = market_provider.holiday_service
    holidays = service.get_holidays("NSE")
    assert isinstance(holidays, list)
    assert service.is_trading_day("NSE", date(2026, 1, 5))
    assert service.is_muhurat("NSE", date(2026, 1, 5)) is False
    assert service.next_trading_day("NSE", date(2026, 1, 24)) == date(2026, 1, 27)


def test_instrument_service_extended(market_provider: MarketMasterProvider) -> None:
    """Instrument service should support save and typed lookups."""
    service = market_provider.instrument_service
    by_type = service.find_by_instrument_type(InstrumentType.INDEX)
    assert len(by_type) >= 5
    instrument = service.get_by_id("NSEFO:NIFTY")
    assert instrument is not None
    assert service.atm_strike("NIFTY", Decimal("24525")) == Decimal("24550")
    assert service.nearest_strike("NIFTY", Decimal("24535")) == Decimal("24550")


def test_instrument_save_and_lookup(market_provider: MarketMasterProvider) -> None:
    """Saving a valid instrument should persist to cache."""
    from app.market.enums import ExchangeCode

    instrument = Instrument(
        instrument_id="NSEFO:TESTIDX",
        trading_symbol="TESTIDX",
        display_name="Test Index",
        underlying="TESTIDX",
        exchange=ExchangeCode.NSEFO,
        segment="FO",
        instrument_type=InstrumentType.INDEX,
        specification=InstrumentSpecification(
            tick_size=Decimal("0.05"),
            lot_size=10,
            freeze_quantity=100,
            strike_interval=Decimal("50"),
        ),
    )
    market_provider.instrument_service.save(instrument)
    saved = market_provider.instrument_service.get_by_id("NSEFO:TESTIDX")
    assert saved is not None
    assert saved.trading_symbol == "TESTIDX"


def test_instrument_save_invalid_raises(market_provider: MarketMasterProvider) -> None:
    """Invalid instruments should fail validation on save."""
    from app.exceptions.validation_exception import ValidationException
    from app.market.enums import ExchangeCode

    instrument = Instrument(
        instrument_id="",
        trading_symbol="BAD",
        display_name="Bad",
        underlying="BAD",
        exchange=ExchangeCode.NSEFO,
        segment="FO",
        instrument_type=InstrumentType.INDEX,
        specification=InstrumentSpecification(
            tick_size=Decimal("0.05"),
            lot_size=10,
            freeze_quantity=100,
            strike_interval=Decimal("50"),
        ),
    )
    with pytest.raises(ValidationException):
        market_provider.instrument_service.save(instrument)
