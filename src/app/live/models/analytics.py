"""Live analytics result models."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.greeks.models.greeks_result import GreeksResult
from app.margin.models.result import MarginResult
from app.option_chain.models.analysis import OptionChainAnalysis
from app.payoff.models.result import PayoffResult
from app.pricing.models.pricing_result import PricingResult
from app.probability.models.probability_result import ProbabilityResult
from app.risk.models.result import RiskResult
from app.volatility.models.volatility_result import VolatilityResult


@dataclass(frozen=True, slots=True)
class LiveAnalyticsSnapshot:
    """Aggregated live analytics for a chain key."""

    underlying: str
    exchange: str
    expiry_date: str
    spot_price: Decimal | None = None
    pricing: PricingResult | None = None
    greeks: GreeksResult | None = None
    volatility: VolatilityResult | None = None
    chain_analysis: OptionChainAnalysis | None = None
    probability: ProbabilityResult | None = None
    payoff: PayoffResult | None = None
    risk: RiskResult | None = None
    margin: MarginResult | None = None
    portfolio_greeks: dict[str, Decimal] | None = None
    position_greeks: dict[str, Decimal] | None = None
    calculation_timestamp: datetime | None = None
