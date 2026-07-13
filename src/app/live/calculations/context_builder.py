"""Build calculation inputs for live analytics."""

from datetime import datetime, timezone

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.services.context_service import CalculationContextService
from app.live.models.chain_key import ChainKey
from app.live.option_chain.chain_builder import ChainBuilder
from app.live.option_chain.chain_manager import OptionChainManager
from app.market_data.models.enums import SnapshotKind
from app.market_data.models.snapshot import MarketSnapshot
from app.option_chain.models.market_snapshot import ChainMarketSnapshot
from app.payoff.models.legs import PortfolioPosition
from app.pricing.models.enums import OptionType
from app.pricing.models.option_contract import OptionContract
from app.volatility.models.snapshots import HistoricalDataSnapshot, VolatilityMarketSnapshot


class LiveContextBuilder:
    """Assemble frozen-engine request inputs from live chain state."""

    def __init__(
        self,
        context_service: CalculationContextService,
        chain_manager: OptionChainManager,
    ) -> None:
        self._context_service = context_service
        self._chain_manager = chain_manager

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

    def build_portfolio(self) -> PortfolioPosition:
        return PortfolioPosition(legs=())
