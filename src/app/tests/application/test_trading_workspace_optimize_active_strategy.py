"""Tests for TradingWorkspaceService.optimize_active_strategy(): the
on-demand "Optimize" action that searches for better variants of whatever
strategy is currently loaded into this session's Trading workspace, sourced
from the same live chain evaluate_active_strategy() uses.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.services.trading_workspace_service import TradingWorkspaceService
from app.application.session.session_manager import SessionManager
from app.live.calculations.evaluation_context import EvaluationContext
from app.live.models.analytics import LiveAnalyticsSnapshot
from app.strategy.builders.strategy_builder import StrategyBuilder
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.strategy import Strategy
from app.strategy_optimizer.models.enums import SearchAlgorithmType


class _FakeLiveAnalyticsPort:
    """LiveAnalyticsPort double: only build_evaluation_context() and
    refresh_and_get_analytics() are exercised by optimize_active_strategy()."""

    def __init__(self, context: EvaluationContext | None, snapshot: LiveAnalyticsSnapshot | None) -> None:
        self.context = context
        self.snapshot = snapshot
        self.context_received: tuple[str, str, str] | None = None
        self.snapshot_received: tuple[str, str, str] | None = None

    def get_chain(self, underlying, exchange, expiry_date):
        raise AssertionError("not exercised")

    def get_analytics(self, underlying, exchange, expiry_date):
        raise AssertionError("not exercised")

    def request_refresh(self, underlying, exchange, expiry_date):
        raise AssertionError("not exercised")

    def refresh_mode(self):
        raise AssertionError("not exercised")

    def build_evaluation_context(self, underlying: str, exchange: str, expiry_date: str):
        self.context_received = (underlying, exchange, expiry_date)
        return self.context

    def refresh_and_get_analytics(self, underlying: str, exchange: str, expiry_date: str):
        self.snapshot_received = (underlying, exchange, expiry_date)
        return self.snapshot


class _RecordingOptimizerEngine:
    def __init__(self) -> None:
        self.received_requests: list = []

    def optimize(self, request):
        self.received_requests.append(request)
        return SimpleNamespace(candidate_strategies=(), overall_score=Decimal("75"))


def _context() -> EvaluationContext:
    return EvaluationContext(
        calculation_context=SimpleNamespace(name="ctx"),
        option_contract=SimpleNamespace(name="contract"),
        option_chain=SimpleNamespace(name="chain"),
        market_snapshot=SimpleNamespace(name="market"),
        chain_market_snapshot=SimpleNamespace(name="chain_market"),
        volatility_market_snapshot=SimpleNamespace(name="vol_market"),
        historical_data=SimpleNamespace(name="historical"),
    )


def _snapshot(*, risk=SimpleNamespace(), margin=SimpleNamespace()) -> LiveAnalyticsSnapshot:
    return LiveAnalyticsSnapshot(
        underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026",
        chain_analysis=SimpleNamespace(name="chain_analysis"),
        volatility=SimpleNamespace(name="volatility"),
        probability=SimpleNamespace(name="probability"),
        risk=risk, margin=margin,
        calculation_timestamp=datetime.now(timezone.utc),
    )


def _leg(**overrides) -> StrategyLeg:
    defaults = dict(
        leg_id="L1", kind=LegKind.CALL_SELL, quantity=195, premium=Decimal("100"),
        strike=Decimal("25000"), underlying="NIFTY", exchange="NFO",
        expiry=date(2026, 8, 18),
    )
    defaults.update(overrides)
    return StrategyLeg(**defaults)


def _strategy(legs: tuple[StrategyLeg, ...]) -> Strategy:
    return Strategy(metadata=StrategyBuilder(name="Test").build().metadata, legs=legs)


def _service_with_active_strategy(
    live_analytics, strategy: Strategy | None, engine: _RecordingOptimizerEngine | None = None,
) -> tuple[TradingWorkspaceService, str, _RecordingOptimizerEngine]:
    sessions = SessionManager()
    cache = WorkspaceCache()
    session = sessions.create(WorkspaceType.TRADING)
    if strategy is not None:
        cache.put_strategy(strategy.strategy_id, strategy)
        sessions.set_active_workspace(session.session_id, WorkspaceType.TRADING, strategy.strategy_id)
    engine = engine or _RecordingOptimizerEngine()
    engines = SimpleNamespace(optimizer=SimpleNamespace(service=engine))
    service = TradingWorkspaceService(
        engines=engines, sessions=sessions, cache=cache, live_analytics=live_analytics,
    )
    return service, session.session_id, engine


class TestOptimizeActiveStrategySuccess:
    def test_returns_optimization_result_on_success(self) -> None:
        port = _FakeLiveAnalyticsPort(_context(), _snapshot())
        strategy = _strategy((_leg(),))
        service, session_id, engine = _service_with_active_strategy(port, strategy)

        result = service.optimize_active_strategy(session_id)

        assert result.success is True
        assert result.message == "Optimization complete"
        assert result.data.overall_score == Decimal("75")  # engine's OptimizationResult, passed through
        assert len(engine.received_requests) == 1

    def test_derives_chain_key_from_first_leg(self) -> None:
        port = _FakeLiveAnalyticsPort(_context(), _snapshot())
        strategy = _strategy((_leg(underlying="BANKNIFTY", exchange="NFO", expiry=date(2026, 9, 24)),))
        service, session_id, _ = _service_with_active_strategy(port, strategy)

        service.optimize_active_strategy(session_id)

        assert port.context_received == ("BANKNIFTY", "NFO", "24-Sep-2026")
        assert port.snapshot_received == ("BANKNIFTY", "NFO", "24-Sep-2026")

    def test_request_uses_simulated_annealing_and_max_pop_objective(self) -> None:
        port = _FakeLiveAnalyticsPort(_context(), _snapshot())
        strategy = _strategy((_leg(),))
        service, session_id, engine = _service_with_active_strategy(port, strategy)

        service.optimize_active_strategy(session_id)

        request = engine.received_requests[0]
        assert request.preferences.search_algorithm == SearchAlgorithmType.SIMULATED_ANNEALING
        from app.strategy_optimizer.models.enums import OptimizationObjective

        assert request.preferences.primary_objective == OptimizationObjective.MAX_POP

    def test_request_carries_real_context_and_engine_results(self) -> None:
        context = _context()
        snapshot = _snapshot()
        port = _FakeLiveAnalyticsPort(context, snapshot)
        strategy = _strategy((_leg(),))
        service, session_id, engine = _service_with_active_strategy(port, strategy)

        service.optimize_active_strategy(session_id)

        request = engine.received_requests[0]
        assert request.calculation_context is context.calculation_context
        assert request.option_chain is context.option_chain
        assert request.option_chain_analysis is snapshot.chain_analysis
        assert request.volatility_result is snapshot.volatility
        assert request.probability_result is snapshot.probability
        assert request.risk_result is snapshot.risk
        assert request.margin_result is snapshot.margin


class TestOptimizeActiveStrategyUnavailableFallsBackGracefully:
    def test_no_active_strategy_returns_failure_without_crashing(self) -> None:
        service, session_id, _ = _service_with_active_strategy(
            _FakeLiveAnalyticsPort(_context(), _snapshot()), None,
        )

        result = service.optimize_active_strategy(session_id)

        assert result.success is False
        assert result.message == "No active strategy to optimize"

    def test_strategy_with_no_legs_returns_failure(self) -> None:
        port = _FakeLiveAnalyticsPort(_context(), _snapshot())
        strategy = _strategy(())
        service, session_id, _ = _service_with_active_strategy(port, strategy)

        result = service.optimize_active_strategy(session_id)

        assert result.success is False
        assert result.message == "Strategy has no legs to optimize"

    def test_leg_missing_expiry_returns_failure(self) -> None:
        port = _FakeLiveAnalyticsPort(_context(), _snapshot())
        strategy = _strategy((_leg(expiry=None),))
        service, session_id, _ = _service_with_active_strategy(port, strategy)

        result = service.optimize_active_strategy(session_id)

        assert result.success is False
        assert result.message == "Strategy legs are missing underlying/expiry"

    def test_chain_unavailable_returns_failure_without_crashing(self) -> None:
        port = _FakeLiveAnalyticsPort(None, _snapshot())  # no evaluation context available
        strategy = _strategy((_leg(),))
        service, session_id, _ = _service_with_active_strategy(port, strategy)

        result = service.optimize_active_strategy(session_id)

        assert result.success is False
        assert "Live chain unavailable" in result.message

    def test_no_risk_result_yet_returns_failure(self) -> None:
        """The strategy hasn't been evaluated yet (payoff/risk/margin are
        only computed for an active strategy with legs) -- Optimize must
        not silently build a request with a missing required field."""
        port = _FakeLiveAnalyticsPort(_context(), _snapshot(risk=None, margin=None))
        strategy = _strategy((_leg(),))
        service, session_id, engine = _service_with_active_strategy(port, strategy)

        result = service.optimize_active_strategy(session_id)

        assert result.success is False
        assert "Live analytics unavailable" in result.message
        assert engine.received_requests == []

    def test_no_live_analytics_port_configured_returns_failure(self) -> None:
        strategy = _strategy((_leg(),))
        sessions = SessionManager()
        cache = WorkspaceCache()
        session = sessions.create(WorkspaceType.TRADING)
        cache.put_strategy(strategy.strategy_id, strategy)
        sessions.set_active_workspace(session.session_id, WorkspaceType.TRADING, strategy.strategy_id)
        engines = SimpleNamespace(optimizer=SimpleNamespace(service=_RecordingOptimizerEngine()))
        service = TradingWorkspaceService(engines=engines, sessions=sessions, cache=cache)

        result = service.optimize_active_strategy(session.session_id)

        assert result.success is False
        assert "Live chain unavailable" in result.message
