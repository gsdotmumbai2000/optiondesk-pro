"""AI analysis request."""

from dataclasses import dataclass

from app.margin.models.result import MarginResult
from app.market_data.models.snapshot import MarketSnapshot
from app.monitor.models.result import MonitorResult
from app.option_chain.models.analysis import OptionChainAnalysis
from app.portfolio.models.result import PortfolioResult
from app.probability.models.probability_result import ProbabilityResult
from app.risk.models.result import RiskResult
from app.strategy.models.evaluation import StrategyEvaluation
from app.strategy_optimizer.models.result import OptimizationResult
from app.volatility.models.volatility_result import VolatilityResult


@dataclass(frozen=True, slots=True)
class RecommendationAnalysisRequest:
    """Immutable input bundle for AI recommendations."""

    session_id: str
    portfolio_result: PortfolioResult
    risk_result: RiskResult | None = None
    margin_result: MarginResult | None = None
    probability_result: ProbabilityResult | None = None
    strategy_evaluation: StrategyEvaluation | None = None
    optimization_result: OptimizationResult | None = None
    position_monitor_result: MonitorResult | None = None
    market_snapshot: MarketSnapshot | None = None
    option_chain_analysis: OptionChainAnalysis | None = None
    volatility_result: VolatilityResult | None = None
