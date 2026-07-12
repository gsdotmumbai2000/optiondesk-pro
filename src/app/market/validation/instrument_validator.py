"""Instrument validator."""

from app.exceptions.validation_exception import ValidationException
from app.market.instrument_master.models import Instrument
from app.market.validation.common import (validate_positive_decimal,
                                          validate_positive_int)


class InstrumentValidator:
    """Validate instrument master records."""

    def validate(self, instrument: Instrument) -> None:
        """Validate an instrument record."""
        if not instrument.instrument_id.strip():
            raise ValidationException("instrument_id is required")
        if not instrument.trading_symbol.strip():
            raise ValidationException("trading_symbol is required")
        if not instrument.underlying.strip():
            raise ValidationException("underlying is required")
        self._validate_specification(instrument)

    def _validate_specification(self, instrument: Instrument) -> None:
        """Validate instrument specification fields."""
        spec = instrument.specification
        validate_positive_int(spec.lot_size, "lot_size")
        validate_positive_int(spec.freeze_quantity, "freeze_quantity")
        validate_positive_decimal(spec.tick_size, "tick_size")
        validate_positive_decimal(spec.strike_interval, "strike_interval")
        if spec.price_precision < 0:
            raise ValidationException("price_precision must be non-negative")
