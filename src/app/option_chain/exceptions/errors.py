"""Option chain engine exceptions."""

from app.exceptions.application_exception import ApplicationException


class OptionChainException(ApplicationException):
    """Raised when option chain engine operations fail."""


class InvalidOptionChainInput(OptionChainException):
    """Raised when option chain inputs fail validation."""
