"""Shared validation helpers for Market Master."""

from decimal import Decimal

from app.exceptions.validation_exception import ValidationException
from app.market.enums import ExchangeCode, InstrumentType


def validate_exchange(exchange: str) -> ExchangeCode:
    """Validate and parse an exchange code."""
    try:
        return ExchangeCode(exchange.upper())
    except ValueError as error:
        raise ValidationException(f"Unsupported exchange: {exchange}") from error


def validate_instrument_type(instrument_type: str) -> InstrumentType:
    """Validate and parse an instrument type."""
    try:
        return InstrumentType(instrument_type.upper())
    except ValueError as error:
        raise ValidationException(
            f"Unsupported instrument type: {instrument_type}"
        ) from error


def validate_positive_int(value: int, field_name: str) -> None:
    """Validate a positive integer field."""
    if value <= 0:
        raise ValidationException(f"{field_name} must be positive")


def validate_positive_decimal(value: Decimal, field_name: str) -> None:
    """Validate a positive decimal field."""
    if value <= 0:
        raise ValidationException(f"{field_name} must be positive")
