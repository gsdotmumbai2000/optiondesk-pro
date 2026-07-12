"""Portfolio analysis request."""

from dataclasses import dataclass

from app.backtesting.models.result import BacktestResult
from app.margin.models.result import MarginResult
from app.market_data.models.snapshot import MarketSnapshot
from app.portfolio.models.broker import BrokerPositionUpdate
from app.portfolio.models.transactions import Trade
from app.risk.models.result import RiskResult
from app.strategy.models.evaluation import StrategyEvaluation


@dataclass(frozen=True, slots=True)
class PortfolioAnalysisRequest:
    """Immutable input bundle for portfolio analytics."""

    portfolio_id: str
    strategy_result: StrategyEvaluation | None = None
    backtest_result: BacktestResult | None = None
    risk_result: RiskResult | None = None
    margin_result: MarginResult | None = None
    market_snapshot: MarketSnapshot | None = None
    trade_executions: tuple[Trade, ...] = ()
    broker_updates: tuple[BrokerPositionUpdate, ...] = ()
