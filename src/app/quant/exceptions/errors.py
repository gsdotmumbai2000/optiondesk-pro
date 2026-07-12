"""Quant engine exceptions."""

from app.exceptions.application_exception import ApplicationException


class QuantException(ApplicationException):
    """Raised when quantitative engine operations fail."""


class InvalidQuantInput(QuantException):
    """Raised when quantitative inputs fail validation."""
