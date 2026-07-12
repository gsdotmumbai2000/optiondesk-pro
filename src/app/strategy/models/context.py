"""Strategy context bundle."""

from dataclasses import dataclass

from app.calculation.context.calculation_context import CalculationContext
from app.greeks.models.greeks_result import GreeksResult
from app.margin.models.result import MarginResult
from app.market_data.models.snapshot import MarketSnapshot
from app.payoff.models.legs import PortfolioPosition
from app.payoff.models.result import PayoffResult
from app.pricing.models.pricing_result import PricingResult
from app.probability.models.probability_result import ProbabilityResult
from app.risk.models.result import RiskResult
from app.strategy.models.leg import StrategyLeg
from app.volatility.models.volatility_result import VolatilityResult


@dataclass(frozen=True, slots=True)
class StrategyContext:
    """Immutable full context after engine orchestration."""

    calculation_context: CalculationContext
    pricing_result: PricingResult
    greeks_result: GreeksResult
    volatility_result: VolatilityResult
    probability_result: ProbabilityResult
    payoff_result: PayoffResult
    risk_result: RiskResult
    margin_result: MarginResult
    legs: tuple[StrategyLeg, ...]
    market_snapshot: MarketSnapshot
    portfolio: PortfolioPosition | None = None
