"""Greeks engine exceptions."""

from app.exceptions.application_exception import ApplicationException


class GreeksException(ApplicationException):
    """Raised when greeks engine operations fail."""


class InvalidGreeksInput(GreeksException):
    """Raised when greeks inputs fail validation."""
