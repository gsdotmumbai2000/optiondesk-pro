"""Application layer exceptions."""

from app.exceptions.application_exception import ApplicationException


class ApplicationLayerException(ApplicationException):
    """Raised when application layer operations fail."""


class InvalidApplicationInput(ApplicationLayerException):
    """Raised when application inputs fail validation."""


class WorkspaceNotFoundError(ApplicationLayerException):
    """Raised when workspace is not active."""


class SessionNotFoundError(ApplicationLayerException):
    """Raised when session does not exist."""
