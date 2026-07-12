"""Backtesting engine exceptions."""

from app.exceptions.application_exception import ApplicationException


class BacktestException(ApplicationException):
    """Raised when backtesting operations fail."""


class InvalidBacktestInput(BacktestException):
    """Raised when backtest inputs fail validation."""
