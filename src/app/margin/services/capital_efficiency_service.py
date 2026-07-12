"""Capital efficiency service."""

from decimal import Decimal

from app.margin.models.optimization import MarginOptimizationResult
from app.margin.models.request import MarginAnalysisRequest
from app.margin.models.result import MarginResult
from app.margin.optimization.margin_optimizer import MarginOptimizer


class CapitalEfficiencyService:
    """Service for capital efficiency analysis."""

    def __init__(self, optimizer: MarginOptimizer | None = None) -> None:
        """Initialize service."""
        self._optimizer = optimizer or MarginOptimizer()

    def analyze(
        self,
        request: MarginAnalysisRequest,
        result: MarginResult,
    ) -> MarginOptimizationResult:
        """Run capital efficiency and optimization analysis."""
        return self._optimizer.optimize(request, result)

    def efficiency_score(self, result: MarginResult) -> Decimal:
        """Return capital efficiency score."""
        return self._optimizer._efficiency_score(result)
