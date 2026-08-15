"""Build calculation inputs for live analytics."""

from datetime import datetime, timezone

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.services.context_service import CalculationContextService
from app.live.calculations.ports import ActiveStrategyPort
from app.live.models.chain_key import ChainKey
from app.live.option_chain.chain_builder import ChainBuilder
from app.live.option_chain.chain_manager import OptionChainManager
from app.market_data.models.enums import SnapshotKind
from app.market_data.models.snapshot import MarketSnapshot
from app.option_chain.models.market_snapshot import ChainMarketSnapshot
from app.payoff.models.legs import PortfolioPosition
from app.pricing.models.enums import OptionType
from app.pricing.models.option_contract import OptionContract
from app.strategy.builders.leg_converter import to_payoff_legs
from app.volatility.models.snapshots import HistoricalDataSnapshot, VolatilityMarketSnapshot


class LiveContextBuilder:
    """Assemble frozen-engine request inputs from live chain state."""

    def __init__(
        self,
        context_service: CalculationContextService,
        chain_manager: OptionChainManager,
        active_strategy: ActiveStrategyPort | None = None,
    ) -> None:
        self._context_service = context_service
        self._chain_manager = chain_manager
        self._active_strategy = active_strategy

    def build_context(self, key: ChainKey) -> CalculationContext:
        return self._context_service.create_context(
            key.underlying,
            key.exchange,
            key.expiry_date,
        )

    def build_option_chain(self, key: ChainKey):
        chain = self._chain_manager.get_chain(key)
        if chain is None:
            raise ValueError(f"Live chain unavailable: {key.cache_key()}")
        return ChainBuilder.to_snapshot(chain)

    def build_contract(self, key: ChainKey, context: CalculationContext) -> OptionContract:
        return OptionContract(
            strike=context.atm_strike,
            option_type=OptionType.CALL,
            expiry=context.expiry,
        )

    def build_market_snapshot(self, key: ChainKey, context: CalculationContext) -> MarketSnapshot:
        return MarketSnapshot(
            snapshot_id=f"live:{key.cache_key()}",
            snapshot_kind=SnapshotKind.CURRENT,
            captured_at=datetime.now(timezone.utc),
        )

    def build_chain_market_snapshot(
        self,
        key: ChainKey,
        context: CalculationContext,
    ) -> ChainMarketSnapshot:
        return ChainMarketSnapshot(
            snapshot_id=f"live-chain:{key.cache_key()}",
            underlying=key.underlying,
            exchange=key.exchange,
            spot_price=context.spot_price,
            captured_at=datetime.now(timezone.utc),
        )

    def build_volatility_snapshot(
        self,
        key: ChainKey,
        context: CalculationContext,
    ) -> VolatilityMarketSnapshot:
        return VolatilityMarketSnapshot(
            snapshot_id=f"live-vol:{key.cache_key()}",
            underlying=key.underlying,
            exchange=key.exchange,
            spot_price=context.spot_price,
            captured_at=datetime.now(timezone.utc),
        )

    def build_historical_snapshot(self, key: ChainKey) -> HistoricalDataSnapshot:
        return HistoricalDataSnapshot(underlying=key.underlying, closes=(), returns=())

    def build_portfolio(self, context: CalculationContext) -> PortfolioPosition:
        """Build the portfolio for this calculation cycle from the currently
        active strategy (looked up fresh via ActiveStrategyPort, never
        cached), converted through the existing to_payoff_legs() adapter --
        the same conversion EngineOrchestrator uses for strategy evaluation.
        Returns an empty portfolio when no strategy is active or no port was
        provided, which is the documented no-active-strategy state.
        """
        if self._active_strategy is None:
            return PortfolioPosition(legs=())
        legs = self._active_strategy.get_active_strategy_legs()
        if not legs:
            return PortfolioPosition(legs=())
        return PortfolioPosition(legs=to_payoff_legs(legs, context))
