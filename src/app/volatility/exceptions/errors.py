"""Volatility engine exceptions."""

from app.exceptions.application_exception import ApplicationException


class VolatilityException(ApplicationException):
    """Raised when volatility engine operations fail."""


class InvalidVolatilityInput(VolatilityException):
    """Raised when volatility inputs fail validation."""
