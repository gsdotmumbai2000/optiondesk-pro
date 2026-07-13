"""Live analytics exception hierarchy."""

from app.exceptions.application_exception import ApplicationException


class LiveAnalyticsException(ApplicationException):
    """Base live analytics error."""


class LiveChainException(LiveAnalyticsException):
    """Raised when live option chain state is invalid."""


class LiveCalculationException(LiveAnalyticsException):
    """Raised when live calculation fails."""


class LiveValidationException(LiveAnalyticsException):
    """Raised when live tick or chain validation fails."""
