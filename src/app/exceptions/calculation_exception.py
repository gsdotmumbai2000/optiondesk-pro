"""Calculation exception."""

from app.exceptions.application_exception import ApplicationException


class CalculationException(ApplicationException):
    """Raised when calculation engine operations fail."""
