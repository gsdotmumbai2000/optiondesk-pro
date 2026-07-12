"""UI exception."""

from app.exceptions.application_exception import ApplicationException


class UIException(ApplicationException):
    """Raised when UI operations fail."""
