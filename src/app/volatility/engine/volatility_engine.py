"""Volatility engine entry point."""

from app.volatility.engine.volatility_calculator import VolatilityCalculator
from app.volatility.models.request import VolatilityAnalysisRequest
from app.volatility.models.volatility_result import VolatilityResult


class VolatilityEngine:
    """Enterprise volatility engine."""

    def __init__(self, calculator: VolatilityCalculator | None = None) -> None:
        """Initialize engine."""
        self._calculator = calculator or VolatilityCalculator()

    @property
    def calculator(self) -> VolatilityCalculator:
        """Return volatility calculator."""
        return self._calculator

    def calculate(self, request: VolatilityAnalysisRequest) -> VolatilityResult:
        """Calculate volatility analytics."""
        return self._calculator.calculate(request)
