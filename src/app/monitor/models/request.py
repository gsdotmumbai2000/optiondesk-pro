"""Monitor analysis request."""

from dataclasses import dataclass

from app.margin.models.result import MarginResult
from app.market_data.models.snapshot import MarketSnapshot
from app.monitor.models.alert import AlertRule
from app.monitor.models.monitor import MarketDataEventRecord
from app.portfolio.models.result import PortfolioResult
from app.probability.models.probability_result import ProbabilityResult
from app.risk.models.result import RiskResult
from app.strategy.models.evaluation import StrategyEvaluation


@dataclass(frozen=True, slots=True)
class MonitorAnalysisRequest:
    """Immutable input bundle for position monitoring."""

    session_id: str
    portfolio_result: PortfolioResult
    risk_result: RiskResult | None = None
    margin_result: MarginResult | None = None
    probability_result: ProbabilityResult | None = None
    strategy_evaluation: StrategyEvaluation | None = None
    market_snapshot: MarketSnapshot | None = None
    market_events: tuple[MarketDataEventRecord, ...] = ()
    rules: tuple[AlertRule, ...] = ()
