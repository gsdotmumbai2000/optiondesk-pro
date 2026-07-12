"""Broker-specific exception hierarchy."""

from app.exceptions.broker_exception import BrokerException


class BrokerConnectionException(BrokerException):
    """Raised when broker connection fails."""


class BrokerAuthenticationException(BrokerException):
    """Raised when broker authentication fails."""


class BrokerSessionExpiredException(BrokerException):
    """Raised when the broker session has expired."""


class BrokerRateLimitException(BrokerException):
    """Raised when broker rate limits are exceeded."""


class BrokerTimeoutException(BrokerException):
    """Raised when a broker request times out."""


class BrokerNotSupportedException(BrokerException):
    """Raised when a broker feature is not supported."""


class BrokerOrderException(BrokerException):
    """Raised when order placement or modification fails."""
