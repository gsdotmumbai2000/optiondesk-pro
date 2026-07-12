"""Pricing engine exceptions."""

from app.exceptions.application_exception import ApplicationException


class PricingException(ApplicationException):
    """Raised when pricing engine operations fail."""


class InvalidPricingInput(PricingException):
    """Raised when pricing inputs fail validation."""


class ExpiredContractException(PricingException):
    """Raised when the option contract has expired."""
