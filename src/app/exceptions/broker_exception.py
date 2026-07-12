"""Broker exception."""

from app.exceptions.application_exception import ApplicationException


class BrokerException(ApplicationException):
    """Raised when broker operations fail."""
