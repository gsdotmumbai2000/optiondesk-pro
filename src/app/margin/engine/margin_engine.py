"""Margin engine entry point."""

from app.margin.engine.margin_calculator import MarginCalculator
from app.margin.engine.margin_estimator import MarginEstimator
from app.margin.models.request import MarginAnalysisRequest
from app.margin.models.result import MarginResult


class MarginEngine:
    """Enterprise margin engine."""

    def __init__(
        self,
        calculator: MarginCalculator | None = None,
        estimator: MarginEstimator | None = None,
    ) -> None:
        """Initialize engine."""
        self._calculator = calculator or MarginCalculator()
        self._estimator = estimator or MarginEstimator()

    @property
    def calculator(self) -> MarginCalculator:
        """Return margin calculator."""
        return self._calculator

    @property
    def estimator(self) -> MarginEstimator:
        """Return margin estimator."""
        return self._estimator

    def calculate(self, request: MarginAnalysisRequest) -> MarginResult:
        """Calculate margin analytics."""
        return self._calculator.calculate(request)

    def estimate(self, request: MarginAnalysisRequest):
        """Estimate margin without full result."""
        return self._estimator.estimate(request)
