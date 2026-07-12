"""Instrument validator tests."""

import pytest

from app.exceptions.validation_exception import ValidationException
from app.market.enums import ExchangeCode, InstrumentType
from app.market.instrument_master.models import (Instrument,
                                                 InstrumentSpecification)
from app.market.instrument_master.validator import InstrumentValidator


def _sample_instrument() -> Instrument:
    """Create a valid sample instrument."""
    return Instrument(
        instrument_id="NSEFO:NIFTY",
        trading_symbol="NIFTY",
        display_name="NIFTY 50",
        underlying="NIFTY",
        exchange=ExchangeCode.NSEFO,
        segment="FO",
        instrument_type=InstrumentType.INDEX,
        specification=InstrumentSpecification(
            tick_size=1,
            lot_size=25,
            freeze_quantity=100,
            strike_interval=50,
        ),
    )


def test_valid_instrument_passes() -> None:
    """Valid instrument should pass validation."""
    InstrumentValidator().validate(_sample_instrument())


def test_invalid_lot_size_fails() -> None:
    """Invalid lot size should fail validation."""
    instrument = _sample_instrument()
    instrument.specification.lot_size = 0
    with pytest.raises(ValidationException):
        InstrumentValidator().validate(instrument)


def test_empty_instrument_id_fails() -> None:
    """Empty instrument_id should fail validation."""
    instrument = _sample_instrument()
    instrument.instrument_id = " "
    with pytest.raises(ValidationException, match="instrument_id"):
        InstrumentValidator().validate(instrument)


def test_empty_trading_symbol_fails() -> None:
    """Empty trading_symbol should fail validation."""
    instrument = _sample_instrument()
    instrument.trading_symbol = ""
    with pytest.raises(ValidationException, match="trading_symbol"):
        InstrumentValidator().validate(instrument)


def test_negative_price_precision_fails() -> None:
    """Negative price_precision should fail validation."""
    instrument = _sample_instrument()
    instrument.specification.price_precision = -1
    with pytest.raises(ValidationException, match="price_precision"):
        InstrumentValidator().validate(instrument)
