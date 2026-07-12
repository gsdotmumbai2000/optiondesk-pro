"""Probability engine entry point."""

from app.probability.engine.probability_calculator import ProbabilityCalculator
from app.probability.models.probability_result import ProbabilityResult
from app.probability.models.request import ProbabilityAnalysisRequest


class ProbabilityEngine:
    """Enterprise probability engine."""

    def __init__(self, calculator: ProbabilityCalculator | None = None) -> None:
        """Initialize engine."""
        self._calculator = calculator or ProbabilityCalculator()

    @property
    def calculator(self) -> ProbabilityCalculator:
        """Return probability calculator."""
        return self._calculator

    def calculate(self, request: ProbabilityAnalysisRequest) -> ProbabilityResult:
        """Calculate probability analytics."""
        return self._calculator.calculate(request)
