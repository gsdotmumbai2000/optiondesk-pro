"""Validation helper and validator tests."""

from datetime import date, time

import pytest

from app.exceptions.validation_exception import ValidationException
from app.market.enums import ExchangeCode, ExpiryType, SessionType
from app.market.expiries.models import ExpiryRecord
from app.market.holidays.models import Holiday
from app.market.sessions.models import TradingSession
from app.market.validation.common import (validate_exchange,
                                          validate_instrument_type,
                                          validate_positive_decimal,
                                          validate_positive_int)
from app.market.validation.expiry_validator import ExpiryValidator
from app.market.validation.holiday_validator import HolidayValidator
from app.market.validation.session_validator import SessionValidator


def test_validate_exchange_success() -> None:
    """Valid exchange codes should parse."""
    assert validate_exchange("nsefo") == ExchangeCode.NSEFO


def test_validate_exchange_failure() -> None:
    """Invalid exchange codes should raise."""
    with pytest.raises(ValidationException, match="Unsupported exchange"):
        validate_exchange("INVALID")


def test_validate_instrument_type_success() -> None:
    """Valid instrument types should parse."""
    from app.market.enums import InstrumentType

    assert validate_instrument_type("option") == InstrumentType.OPTION


def test_validate_instrument_type_failure() -> None:
    """Invalid instrument types should raise."""
    with pytest.raises(ValidationException, match="Unsupported instrument type"):
        validate_instrument_type("BOND")


def test_validate_positive_int_failure() -> None:
    """Non-positive integers should raise."""
    with pytest.raises(ValidationException, match="lot_size"):
        validate_positive_int(0, "lot_size")


def test_validate_positive_decimal_failure() -> None:
    """Non-positive decimals should raise."""
    from decimal import Decimal

    with pytest.raises(ValidationException, match="tick_size"):
        validate_positive_decimal(Decimal("0"), "tick_size")


def test_expiry_validator_success() -> None:
    """Valid expiry records should pass."""
    record = ExpiryRecord(
        underlying="NIFTY",
        expiry_date=date(2026, 1, 30),
        expiry_type=ExpiryType.WEEKLY,
    )
    ExpiryValidator().validate(record, reference_date=date(2026, 1, 1))


def test_expiry_validator_empty_underlying() -> None:
    """Empty underlying should fail."""
    record = ExpiryRecord(
        underlying=" ",
        expiry_date=date(2026, 1, 30),
        expiry_type=ExpiryType.WEEKLY,
    )
    with pytest.raises(ValidationException, match="underlying is required"):
        ExpiryValidator().validate(record)


def test_expiry_validator_before_reference() -> None:
    """Expiry before reference date should fail."""
    record = ExpiryRecord(
        underlying="NIFTY",
        expiry_date=date(2026, 1, 10),
        expiry_type=ExpiryType.WEEKLY,
    )
    with pytest.raises(ValidationException, match="before reference"):
        ExpiryValidator().validate(record, reference_date=date(2026, 1, 15))


def test_holiday_validator_success() -> None:
    """Valid holidays should pass."""
    HolidayValidator().validate(
        Holiday(
            exchange="NSE",
            holiday_date=date(2026, 1, 26),
            holiday_name="Republic Day",
        )
    )


def test_holiday_validator_failures() -> None:
    """Invalid holidays should fail validation."""
    with pytest.raises(ValidationException, match="exchange is required"):
        HolidayValidator().validate(
            Holiday(
                exchange=" ",
                holiday_date=date(2026, 1, 26),
                holiday_name="Republic Day",
            )
        )
    with pytest.raises(ValidationException, match="holiday_name is required"):
        HolidayValidator().validate(
            Holiday(
                exchange="NSE",
                holiday_date=date(2026, 1, 26),
                holiday_name=" ",
            )
        )


def test_session_validator_success() -> None:
    """Valid sessions should pass."""
    SessionValidator().validate(
        TradingSession(
            exchange="NSE",
            session_type=SessionType.REGULAR,
            session_name="Regular",
            start_time=time(9, 15),
            end_time=time(15, 30),
        )
    )


def test_session_validator_failures() -> None:
    """Invalid sessions should fail validation."""
    with pytest.raises(ValidationException, match="exchange is required"):
        SessionValidator().validate(
            TradingSession(
                exchange=" ",
                session_type=SessionType.REGULAR,
                session_name="Regular",
                start_time=time(9, 15),
                end_time=time(15, 30),
            )
        )
    with pytest.raises(ValidationException, match="start_time must be before"):
        SessionValidator().validate(
            TradingSession(
                exchange="NSE",
                session_type=SessionType.REGULAR,
                session_name="Regular",
                start_time=time(15, 30),
                end_time=time(9, 15),
            )
        )
