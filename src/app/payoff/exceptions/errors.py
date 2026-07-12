"""Payoff engine exceptions."""

from app.exceptions.application_exception import ApplicationException


class PayoffException(ApplicationException):
    """Raised when payoff engine operations fail."""


class InvalidPayoffInput(PayoffException):
    """Raised when payoff inputs fail validation."""
