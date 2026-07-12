"""Configuration exception."""

from app.exceptions.application_exception import ApplicationException


class ConfigurationException(ApplicationException):
    """Raised when configuration loading or validation fails."""
