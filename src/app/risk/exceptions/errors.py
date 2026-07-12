"""Risk engine exceptions."""

from app.exceptions.application_exception import ApplicationException


class RiskException(ApplicationException):
    """Raised when risk engine operations fail."""


class InvalidRiskInput(RiskException):
    """Raised when risk inputs fail validation."""
