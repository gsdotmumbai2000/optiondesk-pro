"""Market data exceptions."""

from app.exceptions.application_exception import ApplicationException


class MarketDataException(ApplicationException):
    """Raised when market data operations fail."""


class MarketDataValidationException(MarketDataException):
    """Raised when market data fails validation."""
