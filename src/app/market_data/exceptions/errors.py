"""Market data exception hierarchy."""

from app.exceptions.application_exception import ApplicationException


class MarketDataEngineException(ApplicationException):
    """Base market data engine error."""


class MarketDataConnectionException(MarketDataEngineException):
    """Raised when live feed connection fails."""


class MarketDataSubscriptionException(MarketDataEngineException):
    """Raised when subscription operations fail."""


class MarketDataCacheException(MarketDataEngineException):
    """Raised when cache operations fail."""
