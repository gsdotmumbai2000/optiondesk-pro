"""Margin engine exceptions."""

from app.exceptions.application_exception import ApplicationException


class MarginException(ApplicationException):
    """Raised when margin engine operations fail."""


class InvalidMarginInput(MarginException):
    """Raised when margin inputs fail validation."""
