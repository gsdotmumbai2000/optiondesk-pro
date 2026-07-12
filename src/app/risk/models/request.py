"""Risk analysis request."""

from dataclasses import dataclass

from app.calculation.context.calculation_context import CalculationContext
from app.greeks.models.greeks_result import GreeksResult
from app.market_data.models.snapshot import MarketSnapshot
from app.payoff.models.legs import PortfolioPosition, StrategyLeg
from app.payoff.models.result import PayoffResult
from app.pricing.models.pricing_result import PricingResult
from app.probability.models.probability_result import ProbabilityResult
from app.volatility.models.volatility_result import VolatilityResult


@dataclass(frozen=True, slots=True)
class RiskAnalysisRequest:
    """Immutable input bundle for risk analytics."""

    context: CalculationContext
    pricing_result: PricingResult
    greeks_result: GreeksResult
    volatility_result: VolatilityResult
    probability_result: ProbabilityResult
    payoff_result: PayoffResult
    legs: tuple[StrategyLeg, ...]
    market_snapshot: MarketSnapshot
    portfolio: PortfolioPosition | None = None

    @property
    def resolved_legs(self) -> tuple[StrategyLeg, ...]:
        """Return portfolio legs when provided, otherwise strategy legs."""
        if self.portfolio is not None and self.portfolio.legs:
            return self.portfolio.legs
        return self.legs
