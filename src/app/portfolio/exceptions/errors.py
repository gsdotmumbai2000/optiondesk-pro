"""Portfolio engine exceptions."""

from app.exceptions.application_exception import ApplicationException


class PortfolioException(ApplicationException):
    """Raised when portfolio operations fail."""


class InvalidPortfolioInput(PortfolioException):
    """Raised when portfolio inputs fail validation."""
