"""Option chain analysis request."""

from dataclasses import dataclass

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.models.snapshots import OptionChainSnapshot
from app.greeks.models.greeks_result import GreeksResult
from app.option_chain.models.market_snapshot import ChainMarketSnapshot
from app.volatility.models.volatility_result import VolatilityResult


@dataclass(frozen=True, slots=True)
class OptionChainAnalysisRequest:
    """Immutable input bundle for option chain analytics."""

    context: CalculationContext
    option_chain: OptionChainSnapshot
    greeks_result: GreeksResult
    volatility_result: VolatilityResult
    market_snapshot: ChainMarketSnapshot
