"""Plugin exception."""

from app.exceptions.application_exception import ApplicationException


class PluginException(ApplicationException):
    """Raised when plugin operations fail."""
