"""Raw per-chain evaluation context: the seven pieces StrategyEvaluationRequest
and OptimizationRequest both need (a CalculationContext, a reference option
contract, an option chain snapshot, and four market/volatility/historical
snapshots) -- built the same way LiveCalculationPipeline builds them for a
tick, just returned raw instead of fed straight into the frozen engines."""

from dataclasses import dataclass

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.models.snapshots import OptionChainSnapshot
from app.market_data.models.snapshot import MarketSnapshot
from app.option_chain.models.market_snapshot import ChainMarketSnapshot
from app.pricing.models.option_contract import OptionContract
from app.volatility.models.snapshots import HistoricalDataSnapshot, VolatilityMarketSnapshot


@dataclass(frozen=True, slots=True)
class EvaluationContext:
    """Bundle of raw context pieces for one chain key."""

    calculation_context: CalculationContext
    option_contract: OptionContract
    option_chain: OptionChainSnapshot
    market_snapshot: MarketSnapshot
    chain_market_snapshot: ChainMarketSnapshot
    volatility_market_snapshot: VolatilityMarketSnapshot
    historical_data: HistoricalDataSnapshot
