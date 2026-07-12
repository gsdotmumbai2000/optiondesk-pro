"""Validation exception."""

from app.exceptions.application_exception import ApplicationException


class ValidationException(ApplicationException):
    """Raised when input validation fails."""
