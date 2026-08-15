"""Regression tests for wiring the active strategy into the live calculation
pipeline (Task 17).

Covers, per the required test plan:
  1. active strategy legs reach the pipeline
  2. legs=() regression proof against the real PayoffValidator
  3. BUY/SELL mapping
  4. multiple legs preserved
  5. active strategy change is reflected on the next lookup (no stale cache)
  6. no active strategy behaves as a defined no-op, no crash
  7. quantity semantics pass through unchanged (no invented lot-size math)
  8. option leg expiry is preserved, never overwritten by the chain's expiry
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.session.session_manager import SessionManager
from app.calculation.context.calculation_context import CalculationContext
from app.calculation.factory.context_factory import CalculationContextFactory
from app.calculation.providers.dividend_provider import DividendProvider
from app.calculation.providers.expiry_provider import ExpiryProvider
from app.calculation.providers.interest_rate_provider import InterestRateProvider
from app.calculation.providers.market_status_provider import MarketStatusProvider
from app.calculation.providers.time_provider import TimeProvider
from app.calculation.providers.volatility_provider import VolatilityProvider
from app.live.calculations.active_strategy_adapter import ActiveStrategyAdapter
from app.live.calculations.context_builder import LiveContextBuilder
from app.live.calculations.pipeline import LiveCalculationPipeline
from app.live.models.chain_key import ChainKey
from app.payoff.bootstrap import PayoffProvider
from app.payoff.exceptions import InvalidPayoffInput
from app.payoff.models.legs import PortfolioPosition
from app.payoff.models.request import PayoffAnalysisRequest
from app.strategy.builders.strategy_builder import StrategyBuilder
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.strategy import Strategy


# --- Reused fixture pattern from test_context_factory_spot_exchange.py ---
# (duplicated locally to keep this test file self-contained; same fakes).


@dataclass
class _RecordingMarketData:
    def get_spot(self, symbol: str, exchange: str):
        return SimpleNamespace(symbol=symbol, exchange=exchange, ltp=Decimal("24400"))

    def get_future(self, symbol: str, exchange: str, expiry_date: str):
        return SimpleNamespace(
            symbol=symbol,
            exchange=exchange,
            underlying=symbol,
            expiry_date=expiry_date,
            ltp=Decimal("24450"),
        )

    def get_option_chain(self, underlying: str, exchange: str, expiry_date: str):
        return SimpleNamespace(
            underlying=underlying,
            exchange=exchange,
            expiry_date=expiry_date,
            spot_price=Decimal("24400"),
            atm_strike=Decimal("24400"),
            strikes=(),
        )

    def get_atm_strike(self, underlying: str, exchange: str, expiry_date: str):
        return Decimal("24400")


class _FixedInstruments:
    def get_lot_size(self, underlying: str) -> int:
        return 75

    def get_tick_size(self, underlying: str) -> Decimal:
        return Decimal("0.05")

    def get_strike_interval(self, underlying: str) -> Decimal:
        return Decimal("50")


class _FixedExpiryCalendar:
    def calculate_dte(self, exchange: str, from_date: date, expiry_date: date) -> int:
        return max((expiry_date - from_date).days, 0)

    def calculate_tte_seconds(self, exchange: str, now: datetime, expiry_date: date) -> int:
        return 3600

    def nearest_monthly_expiry(self, underlying: str, exchange: str, on_date: date):
        return on_date + timedelta(days=21)


class _AlwaysOpenMarketStatus:
    def is_market_open(self, exchange: str, moment: datetime) -> bool:
        return True

    def trade_date(self, exchange: str, moment: datetime) -> date:
        return moment.date()


def _real_calculation_context() -> CalculationContext:
    """A real, fully-valid CalculationContext for NIFTY/NFO, built the same
    way test_context_factory_spot_exchange.py does."""
    factory = CalculationContextFactory(
        _RecordingMarketData(),
        _FixedInstruments(),
        ExpiryProvider(_FixedExpiryCalendar()),
        InterestRateProvider(),
        DividendProvider(),
        VolatilityProvider(),
        MarketStatusProvider(_AlwaysOpenMarketStatus(), TimeProvider()),
    )
    option_expiry = datetime.now(timezone.utc).date() + timedelta(days=7)
    return factory.build("NIFTY", "NFO", option_expiry.strftime("%d-%b-%Y"))


def _strategy_leg(
    leg_id: str,
    kind: LegKind,
    quantity: int,
    *,
    strike: Decimal = Decimal("24400"),
    expiry: date | None = None,
    premium: Decimal = Decimal("100"),
) -> StrategyLeg:
    return StrategyLeg(
        leg_id=leg_id,
        kind=kind,
        quantity=quantity,
        premium=premium,
        strike=strike,
        expiry=expiry,
        underlying="NIFTY",
        exchange="NFO",
    )


class _FakeActiveStrategyPort:
    """Test double for ActiveStrategyPort: returns whatever legs are set,
    re-read on every call (never cached by the port itself)."""

    def __init__(self, legs: tuple[StrategyLeg, ...] = ()) -> None:
        self.legs = legs
        self.call_count = 0

    def get_active_strategy_legs(self) -> tuple[StrategyLeg, ...]:
        self.call_count += 1
        return self.legs


# --- 1/5/6: ActiveStrategyAdapter resolution against real session/cache state ---


class TestActiveStrategyAdapterResolution:
    def _make(self) -> tuple[ActiveStrategyAdapter, SessionManager, WorkspaceCache]:
        sessions = SessionManager()
        cache = WorkspaceCache()
        return ActiveStrategyAdapter(sessions, cache), sessions, cache

    def test_no_active_strategy_returns_empty_tuple(self) -> None:
        adapter, _, _ = self._make()

        assert adapter.get_active_strategy_legs() == ()

    def test_active_strategy_with_one_leg_is_returned(self) -> None:
        adapter, sessions, cache = self._make()
        session = sessions.create(WorkspaceType.TRADING)
        leg = _strategy_leg("L1", LegKind.CALL_BUY, 1)
        strategy = Strategy(
            metadata=StrategyBuilder(name="Test").build().metadata,
            legs=(leg,),
        )
        cache.put_strategy(strategy.strategy_id, strategy)
        sessions.set_active_workspace(session.session_id, WorkspaceType.TRADING, strategy.strategy_id)

        legs = adapter.get_active_strategy_legs()

        assert legs == (leg,)

    def test_active_strategy_change_is_reflected_on_next_lookup(self) -> None:
        """Dynamic lookup: constructing the adapter before any strategy is
        active, then activating one, then switching to another, must never
        return a value captured earlier -- proves no stale internal cache."""
        adapter, sessions, cache = self._make()
        session = sessions.create(WorkspaceType.TRADING)

        assert adapter.get_active_strategy_legs() == ()  # adapter pre-dates any strategy

        leg_a = _strategy_leg("A1", LegKind.CALL_BUY, 1)
        strategy_a = Strategy(metadata=StrategyBuilder(name="A").build().metadata, legs=(leg_a,))
        cache.put_strategy(strategy_a.strategy_id, strategy_a)
        sessions.set_active_workspace(session.session_id, WorkspaceType.TRADING, strategy_a.strategy_id)
        assert adapter.get_active_strategy_legs() == (leg_a,)

        leg_b = _strategy_leg("B1", LegKind.PUT_SELL, 2)
        strategy_b = Strategy(metadata=StrategyBuilder(name="B").build().metadata, legs=(leg_b,))
        cache.put_strategy(strategy_b.strategy_id, strategy_b)
        sessions.set_active_workspace(session.session_id, WorkspaceType.TRADING, strategy_b.strategy_id)

        legs = adapter.get_active_strategy_legs()

        assert legs == (leg_b,)  # reflects the newly active strategy, not strategy_a


# --- 2/3/4/7/8: LiveContextBuilder.build_portfolio() leg mapping ---


class TestLiveContextBuilderBuildPortfolio:
    def _builder(self, port) -> LiveContextBuilder:
        return LiveContextBuilder(
            context_service=None,  # not exercised by build_portfolio()
            chain_manager=None,
            active_strategy=port,
        )

    def test_no_port_returns_empty_portfolio(self) -> None:
        builder = LiveContextBuilder(context_service=None, chain_manager=None)
        ctx = _real_calculation_context()

        portfolio = builder.build_portfolio(ctx)

        assert portfolio == PortfolioPosition(legs=())

    def test_no_active_strategy_returns_empty_portfolio(self) -> None:
        builder = self._builder(_FakeActiveStrategyPort(legs=()))
        ctx = _real_calculation_context()

        portfolio = builder.build_portfolio(ctx)

        assert portfolio.legs == ()

    def test_single_buy_leg_maps_to_positive_quantity(self) -> None:
        leg = _strategy_leg("L1", LegKind.CALL_BUY, 3, expiry=date(2026, 8, 18))
        builder = self._builder(_FakeActiveStrategyPort(legs=(leg,)))
        ctx = _real_calculation_context()

        portfolio = builder.build_portfolio(ctx)

        assert len(portfolio.legs) == 1
        resolved = portfolio.legs[0]
        assert resolved.quantity == 3  # BUY -> positive, unchanged magnitude

    def test_single_sell_leg_maps_to_negative_quantity(self) -> None:
        leg = _strategy_leg("L1", LegKind.PUT_SELL, 3, expiry=date(2026, 8, 18))
        builder = self._builder(_FakeActiveStrategyPort(legs=(leg,)))
        ctx = _real_calculation_context()

        portfolio = builder.build_portfolio(ctx)

        resolved = portfolio.legs[0]
        assert resolved.quantity == -3  # SELL -> negative, same magnitude

    def test_buy_and_sell_produce_distinct_signed_quantities(self) -> None:
        buy_leg = _strategy_leg("B", LegKind.CALL_BUY, 5, expiry=date(2026, 8, 18))
        sell_leg = _strategy_leg("S", LegKind.CALL_SELL, 5, expiry=date(2026, 8, 18))
        builder = self._builder(_FakeActiveStrategyPort(legs=(buy_leg, sell_leg)))
        ctx = _real_calculation_context()

        portfolio = builder.build_portfolio(ctx)

        quantities = {leg.quantity for leg in portfolio.legs}
        assert quantities == {5, -5}

    def test_multiple_legs_all_preserved(self) -> None:
        legs = (
            _strategy_leg("L1", LegKind.CALL_BUY, 1, strike=Decimal("24500"), expiry=date(2026, 8, 18)),
            _strategy_leg("L2", LegKind.CALL_SELL, 1, strike=Decimal("24600"), expiry=date(2026, 8, 18)),
            _strategy_leg("L3", LegKind.PUT_BUY, 1, strike=Decimal("24300"), expiry=date(2026, 8, 18)),
            _strategy_leg("L4", LegKind.PUT_SELL, 1, strike=Decimal("24200"), expiry=date(2026, 8, 18)),
        )
        builder = self._builder(_FakeActiveStrategyPort(legs=legs))
        ctx = _real_calculation_context()

        portfolio = builder.build_portfolio(ctx)

        assert len(portfolio.legs) == 4  # iron-condor-shaped: all 4 legs reach the engine

    def test_quantity_passes_through_unchanged_no_invented_lot_size(self) -> None:
        """to_payoff_legs() does not multiply by lot size/multiplier; the
        live pipeline must not add new lot-size math at this boundary."""
        leg = _strategy_leg("L1", LegKind.CALL_BUY, 7, expiry=date(2026, 8, 18))
        builder = self._builder(_FakeActiveStrategyPort(legs=(leg,)))
        ctx = _real_calculation_context()  # lot_size=75 in this fixture

        portfolio = builder.build_portfolio(ctx)

        assert portfolio.legs[0].quantity == 7  # not 7 * 75

    def test_leg_expiry_is_preserved_not_overwritten_by_context_expiry(self) -> None:
        """The strategy leg's own expiry must survive, even though the live
        CalculationContext (ctx.expiry) is built for a different (weekly
        option chain) expiry key -- to_payoff_legs() only falls back to
        context.expiry when a leg omits its own."""
        leg_expiry = date(2026, 9, 24)  # deliberately different from ctx.expiry
        leg = _strategy_leg("L1", LegKind.CALL_BUY, 1, expiry=leg_expiry)
        builder = self._builder(_FakeActiveStrategyPort(legs=(leg,)))
        ctx = _real_calculation_context()
        assert ctx.expiry != leg_expiry  # sanity: context has its own (different) expiry

        portfolio = builder.build_portfolio(ctx)

        assert portfolio.legs[0].expiry == leg_expiry  # leg's own expiry wins
        assert portfolio.legs[0].expiry != ctx.expiry

    def test_leg_without_expiry_falls_back_to_context_expiry(self) -> None:
        """Existing to_payoff_legs() fallback behavior, unmodified -- only a
        leg that omits its own expiry uses the context's."""
        leg = _strategy_leg("L1", LegKind.CALL_BUY, 1, expiry=None)
        builder = self._builder(_FakeActiveStrategyPort(legs=(leg,)))
        ctx = _real_calculation_context()

        portfolio = builder.build_portfolio(ctx)

        assert portfolio.legs[0].expiry == ctx.expiry


# --- Fakes for pipeline-level tests: record what each request received. ---


class _FakeLiveContextBuilder:
    """Duck-typed LiveContextBuilder stand-in: returns simple canned
    snapshots for every stage except build_portfolio(), which this test
    controls directly to isolate pipeline wiring from context assembly
    (already covered by TestLiveContextBuilderBuildPortfolio above)."""

    def __init__(self, portfolio: PortfolioPosition) -> None:
        self._portfolio = portfolio
        self.ctx = _real_calculation_context()

    def build_context(self, key):
        return self.ctx

    def build_contract(self, key, context):
        return SimpleNamespace(strike=context.atm_strike, option_type=None, expiry=context.expiry)

    def build_option_chain(self, key):
        return SimpleNamespace()

    def build_market_snapshot(self, key, context):
        return SimpleNamespace(snapshot_id=f"live:{key.cache_key()}")

    def build_chain_market_snapshot(self, key, context):
        return SimpleNamespace()

    def build_volatility_snapshot(self, key, context):
        return SimpleNamespace()

    def build_historical_snapshot(self, key):
        return SimpleNamespace()

    def build_portfolio(self, context):
        return self._portfolio


class _RecordingEngine:
    """Generic fake engine port: records the request it received and
    returns a simple canned result."""

    def __init__(self, result_factory=lambda: SimpleNamespace()) -> None:
        self.requests: list = []
        self._result_factory = result_factory

    def calculate(self, request):
        self.requests.append(request)
        return self._result_factory()

    def analyze(self, request):
        self.requests.append(request)
        return self._result_factory()

    # pricing/greeks use different method names
    def price(self, context, contract):
        self.requests.append((context, contract))
        return SimpleNamespace(theoretical_price=Decimal("10"))

    def calculate_greeks(self, context, contract, pricing_result):
        self.requests.append((context, contract, pricing_result))
        return SimpleNamespace(delta=Decimal("0.5"), gamma=Decimal("0.1"), theta=Decimal("-1"), vega=Decimal("2"))


def _fake_engine_bundle():
    pricing = _RecordingEngine()
    greeks = _RecordingEngine()
    volatility = _RecordingEngine(lambda: SimpleNamespace())
    option_chain = _RecordingEngine(lambda: SimpleNamespace())
    probability = _RecordingEngine(lambda: SimpleNamespace())
    payoff = _RecordingEngine(lambda: SimpleNamespace(current_pnl=Decimal("0")))
    risk = _RecordingEngine(lambda: SimpleNamespace(capital_at_risk=Decimal("0")))
    margin = _RecordingEngine(lambda: SimpleNamespace())
    return SimpleNamespace(
        pricing=pricing,
        greeks=greeks,
        volatility=volatility,
        option_chain=option_chain,
        probability=probability,
        payoff=payoff,
        risk=risk,
        margin=margin,
    )


# --- 1/4/6: legs reach Payoff/Risk/Margin consistently; no-op when empty ---


class TestLiveCalculationPipelineLegsFlow:
    def _key(self) -> ChainKey:
        return ChainKey(underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026")

    def test_resolved_legs_reach_payoff_risk_margin_requests(self) -> None:
        legs = (
            _strategy_leg("L1", LegKind.CALL_BUY, 1, expiry=date(2026, 8, 18)),
            _strategy_leg("L2", LegKind.PUT_SELL, 2, expiry=date(2026, 8, 18)),
        )
        from app.strategy.builders.leg_converter import to_payoff_legs

        ctx = _real_calculation_context()
        resolved = to_payoff_legs(legs, ctx)
        portfolio = PortfolioPosition(legs=resolved)
        context_builder = _FakeLiveContextBuilder(portfolio)
        engines = _fake_engine_bundle()
        pipeline = LiveCalculationPipeline(engines, context_builder)

        snapshot = pipeline.run(self._key())

        assert len(engines.payoff.requests) == 1
        assert len(engines.risk.requests) == 1
        assert len(engines.margin.requests) == 1
        assert engines.payoff.requests[0].legs == resolved
        assert engines.risk.requests[0].legs == resolved
        assert engines.margin.requests[0].legs == resolved
        assert len(engines.payoff.requests[0].legs) == 2
        assert snapshot.payoff is not None
        assert snapshot.risk is not None
        assert snapshot.margin is not None

    def test_no_active_strategy_skips_payoff_risk_margin_without_crash(self) -> None:
        context_builder = _FakeLiveContextBuilder(PortfolioPosition(legs=()))
        engines = _fake_engine_bundle()
        pipeline = LiveCalculationPipeline(engines, context_builder)

        snapshot = pipeline.run(self._key())  # must not raise

        assert engines.payoff.requests == []
        assert engines.risk.requests == []
        assert engines.margin.requests == []
        assert snapshot.payoff is None
        assert snapshot.risk is None
        assert snapshot.margin is None
        # pricing/greeks/volatility/chain/probability still ran (no regression)
        assert len(engines.pricing.requests) == 1
        assert len(engines.greeks.requests) == 1
        assert len(engines.volatility.requests) == 1
        assert len(engines.option_chain.requests) == 1
        assert len(engines.probability.requests) == 1

    def test_same_portfolio_used_consistently_across_requests(self) -> None:
        leg = _strategy_leg("L1", LegKind.CALL_BUY, 1, expiry=date(2026, 8, 18))
        from app.strategy.builders.leg_converter import to_payoff_legs

        ctx = _real_calculation_context()
        resolved = to_payoff_legs((leg,), ctx)
        portfolio = PortfolioPosition(legs=resolved)
        context_builder = _FakeLiveContextBuilder(portfolio)
        engines = _fake_engine_bundle()
        pipeline = LiveCalculationPipeline(engines, context_builder)

        pipeline.run(self._key())

        assert engines.payoff.requests[0].portfolio is portfolio
        assert engines.risk.requests[0].portfolio is portfolio
        assert engines.margin.requests[0].portfolio is portfolio


# --- 2: prove the historical legs=() failure against the REAL validator ---


class TestEmptyLegsRegressionAgainstRealValidator:
    def _valid_payoff_request(self, legs) -> PayoffAnalysisRequest:
        ctx = _real_calculation_context()
        return PayoffAnalysisRequest(
            context=ctx,
            pricing_result=SimpleNamespace(theoretical_price=Decimal("10")),
            greeks_result=SimpleNamespace(delta=Decimal("0.5")),
            volatility_result=SimpleNamespace(implied_volatility=Decimal("0.2")),
            probability_result=SimpleNamespace(expected_value=Decimal("1")),
            legs=legs,
            portfolio=None,
        )

    def test_legs_empty_raises_invalid_payoff_input(self) -> None:
        """This is the exact historical failure: PayoffService.calculate()
        (the real frozen engine, unmodified) rejects legs=() with
        'portfolio must include at least one leg'. The live pipeline must
        never construct a request like this once a strategy is active."""
        request = self._valid_payoff_request(())

        with pytest.raises(InvalidPayoffInput, match="at least one leg"):
            PayoffProvider().service.calculate(request)

    def test_legs_non_empty_passes_validation(self) -> None:
        leg = _strategy_leg("L1", LegKind.CALL_BUY, 1, expiry=date(2026, 8, 18))
        from app.strategy.builders.leg_converter import to_payoff_legs

        ctx = _real_calculation_context()
        resolved = to_payoff_legs((leg,), ctx)
        request = self._valid_payoff_request(resolved)

        result = PayoffProvider().service.calculate(request)  # must not raise

        assert result is not None
