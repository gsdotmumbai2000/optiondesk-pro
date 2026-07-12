"""Strategy optimizer exceptions."""

from app.exceptions.application_exception import ApplicationException


class OptimizerException(ApplicationException):
    """Raised when optimizer operations fail."""


class InvalidOptimizerInput(OptimizerException):
    """Raised when optimizer inputs fail validation."""
