"""Optimization request bundle."""

from dataclasses import dataclass

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.models.snapshots import OptionChainSnapshot
from app.margin.models.result import MarginResult
from app.market_data.models.snapshot import MarketSnapshot
from app.option_chain.models.analysis import OptionChainAnalysis
from app.option_chain.models.market_snapshot import ChainMarketSnapshot
from app.pricing.models.option_contract import OptionContract
from app.probability.models.probability_result import ProbabilityResult
from app.risk.models.result import RiskResult
from app.strategy.models.context import StrategyContext
from app.strategy_optimizer.models.constraints import OptimizationConstraints
from app.strategy_optimizer.models.preferences import OptimizationPreferences
from app.volatility.models.snapshots import (
    HistoricalDataSnapshot,
    VolatilityMarketSnapshot,
)
from app.volatility.models.volatility_result import VolatilityResult


@dataclass(frozen=True, slots=True)
class OptimizationRequest:
    """Immutable input bundle for strategy optimization."""

    calculation_context: CalculationContext
    strategy_context: StrategyContext | None
    market_snapshot: MarketSnapshot
    option_chain_analysis: OptionChainAnalysis
    volatility_result: VolatilityResult
    probability_result: ProbabilityResult
    risk_result: RiskResult
    margin_result: MarginResult
    preferences: OptimizationPreferences
    constraints: OptimizationConstraints
    option_contract: OptionContract
    option_chain: OptionChainSnapshot
    chain_market_snapshot: ChainMarketSnapshot
    volatility_market_snapshot: VolatilityMarketSnapshot
    historical_data: HistoricalDataSnapshot
