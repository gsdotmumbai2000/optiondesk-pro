"""Probability calculator."""

from datetime import datetime, timezone
from decimal import Decimal

from app.probability.analytics.expected_value import expected_value as calc_expected_value
from app.probability.analytics.pop import probability_of_profit as calc_pop
from app.probability.models.enums import ProbabilityModelVersion
from app.probability.models.probability_result import ProbabilityResult
from app.probability.models.request import ProbabilityAnalysisRequest


class ProbabilityCalculator:
    """Calculate probability analytics from request bundle."""

    def calculate(self, request: ProbabilityAnalysisRequest) -> ProbabilityResult:
        """Compute ProbabilityResult from request."""
        pop = calc_pop(request.pricing_result)
        ev = calc_expected_value(
            request.pricing_result,
            request.volatility_result,
            request.chain_analysis,
        )
        touch = min(pop + Decimal("0.15"), Decimal("1"))
        return ProbabilityResult(
            expected_value=ev,
            probability_of_profit=pop,
            probability_of_touch=touch,
            calculation_timestamp=datetime.now(timezone.utc),
            model_version=ProbabilityModelVersion.V1,
        )
