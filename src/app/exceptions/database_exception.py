"""Database exception."""

from app.exceptions.application_exception import ApplicationException


class DatabaseException(ApplicationException):
    """Raised when database operations fail."""
