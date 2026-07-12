"""Calculation engine exceptions."""

from app.exceptions.calculation_exception import CalculationException


class InvalidContextException(CalculationException):
    """Raised when a calculation context fails validation."""


class MissingMarketDataException(CalculationException):
    """Raised when required market data is unavailable."""


class InvalidExpiryException(CalculationException):
    """Raised when expiry data is invalid."""
