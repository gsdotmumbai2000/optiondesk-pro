"""Payoff engine entry point."""

from app.payoff.engine.payoff_calculator import PayoffCalculator
from app.payoff.models.request import PayoffAnalysisRequest
from app.payoff.models.result import PayoffResult


class PayoffEngine:
    """Enterprise payoff engine."""

    def __init__(self, calculator: PayoffCalculator | None = None) -> None:
        """Initialize engine."""
        self._calculator = calculator or PayoffCalculator()

    @property
    def calculator(self) -> PayoffCalculator:
        """Return payoff calculator."""
        return self._calculator

    def calculate(self, request: PayoffAnalysisRequest) -> PayoffResult:
        """Calculate payoff analytics."""
        return self._calculator.calculate(request)
