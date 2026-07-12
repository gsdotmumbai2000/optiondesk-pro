"""Strategy engine exceptions."""

from app.exceptions.application_exception import ApplicationException


class StrategyException(ApplicationException):
    """Raised when strategy engine operations fail."""


class InvalidStrategyInput(StrategyException):
    """Raised when strategy inputs fail validation."""
