"""Monitor engine exceptions."""

from app.exceptions.application_exception import ApplicationException


class MonitorException(ApplicationException):
    """Raised when monitor operations fail."""


class InvalidMonitorInput(MonitorException):
    """Raised when monitor inputs fail validation."""
