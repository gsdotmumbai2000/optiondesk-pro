"""Probability engine exceptions."""

from app.exceptions.application_exception import ApplicationException


class ProbabilityException(ApplicationException):
    """Raised when probability engine operations fail."""


class InvalidProbabilityInput(ProbabilityException):
    """Raised when probability inputs fail validation."""
