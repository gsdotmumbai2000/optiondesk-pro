"""Strategy evaluation request."""

from dataclasses import dataclass

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.models.snapshots import OptionChainSnapshot
from app.margin.models.broker_response import BrokerMarginResponse
from app.market_data.models.snapshot import MarketSnapshot
from app.option_chain.models.market_snapshot import ChainMarketSnapshot
from app.payoff.models.legs import PortfolioPosition
from app.pricing.models.option_contract import OptionContract
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.strategy import Strategy
from app.volatility.models.snapshots import (
    HistoricalDataSnapshot,
    VolatilityMarketSnapshot,
)


@dataclass(frozen=True, slots=True)
class StrategyEvaluationRequest:
    """Input bundle for strategy evaluation orchestration."""

    strategy: Strategy
    calculation_context: CalculationContext
    option_contract: OptionContract
    option_chain: OptionChainSnapshot
    market_snapshot: MarketSnapshot
    chain_market_snapshot: ChainMarketSnapshot
    volatility_market_snapshot: VolatilityMarketSnapshot
    historical_data: HistoricalDataSnapshot
    portfolio: PortfolioPosition | None = None
    broker_response: BrokerMarginResponse | None = None

    @property
    def legs(self) -> tuple[StrategyLeg, ...]:
        """Return strategy legs."""
        return self.strategy.legs
