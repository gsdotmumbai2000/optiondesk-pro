"""Margin analysis request."""

from dataclasses import dataclass

from app.calculation.context.calculation_context import CalculationContext
from app.margin.models.broker_response import BrokerMarginResponse
from app.market_data.models.snapshot import MarketSnapshot
from app.payoff.models.legs import PortfolioPosition, StrategyLeg
from app.payoff.models.result import PayoffResult
from app.risk.models.result import RiskResult


@dataclass(frozen=True, slots=True)
class MarginAnalysisRequest:
    """Immutable input bundle for margin analytics."""

    context: CalculationContext
    legs: tuple[StrategyLeg, ...]
    risk_result: RiskResult
    payoff_result: PayoffResult
    market_snapshot: MarketSnapshot
    broker_response: BrokerMarginResponse | None = None
    portfolio: PortfolioPosition | None = None

    @property
    def resolved_legs(self) -> tuple[StrategyLeg, ...]:
        """Return portfolio legs when provided, otherwise strategy legs."""
        if self.portfolio is not None and self.portfolio.legs:
            return self.portfolio.legs
        return self.legs
