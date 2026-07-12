"""AI engine exceptions."""

from app.exceptions.application_exception import ApplicationException


class AIException(ApplicationException):
    """Raised when AI recommendation operations fail."""


class InvalidRecommendationInput(AIException):
    """Raised when AI inputs fail validation."""


class MissingEvidenceError(AIException):
    """Raised when recommendation lacks supporting evidence."""
