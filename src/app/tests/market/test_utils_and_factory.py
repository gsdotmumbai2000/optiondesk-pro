"""Utility and factory tests."""

from datetime import date, datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.market.enums import ExchangeCode, InstrumentType
from app.market.instrument_master.factory import InstrumentFactory
from app.market.utils.dte_utils import calculate_dte, calculate_tte
from app.market.utils.strike_utils import (itm_strike, next_strike, otm_strike,
                                           previous_strike, round_strike)


def test_dte_zero_when_expired() -> None:
    """DTE should be zero when expiry is not after from_date."""
    trading_days = {date(2026, 1, 5)}
    assert calculate_dte(date(2026, 1, 10), date(2026, 1, 5), trading_days) == 0


def test_dte_counts_trading_days() -> None:
    """DTE should count only trading days."""
    trading_days = {date(2026, 1, 6), date(2026, 1, 7)}
    assert calculate_dte(date(2026, 1, 5), date(2026, 1, 7), trading_days) == 2


def test_tte_after_market_close() -> None:
    """TTE should be zero after market close on expiry day."""
    tz = ZoneInfo("Asia/Kolkata")
    now = datetime(2026, 1, 30, 16, 0, tzinfo=tz)
    assert (
        calculate_tte(now, date(2026, 1, 30), time(15, 30), timezone="Asia/Kolkata")
        == 0
    )


def test_tte_before_market_close() -> None:
    """TTE should be positive before market close."""
    tz = ZoneInfo("Asia/Kolkata")
    now = datetime(2026, 1, 30, 10, 0, tzinfo=tz)
    tte = calculate_tte(now, date(2026, 1, 30), time(15, 30), timezone="Asia/Kolkata")
    assert tte > 0


def test_strike_edge_cases() -> None:
    """Strike helpers should handle edge cases."""
    interval = Decimal("50")
    assert round_strike(Decimal("100"), Decimal("0")) == Decimal("100")
    assert next_strike(Decimal("24550"), interval) == Decimal("24600")
    assert previous_strike(Decimal("24550"), interval) == Decimal("24500")
    assert otm_strike(Decimal("24500"), interval, option_right="PE") == Decimal("24450")
    assert itm_strike(Decimal("24500"), interval, option_right="CE") == Decimal("24450")


def test_instrument_factory_placeholder() -> None:
    """Placeholder instruments should be inactive."""
    instrument = InstrumentFactory.placeholder(
        "GOLD",
        exchange=ExchangeCode.MCX,
        instrument_type=InstrumentType.COMMODITY,
        category="Commodity",
    )
    assert instrument.is_active is False
    assert "Commodity" in instrument.display_name
