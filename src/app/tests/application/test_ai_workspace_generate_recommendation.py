"""Tests for AIWorkspaceService.generate_recommendation_for_active_strategy():
the on-demand "Generate Recommendation" action that builds a real
RecommendationAnalysisRequest for whatever strategy is currently loaded
into this session's Trading workspace.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.services.ai_workspace_service import AIWorkspaceService
from app.application.session.session_manager import SessionManager
from app.live.calculations.evaluation_context import EvaluationContext
from app.live.models.analytics import LiveAnalyticsSnapshot
from app.strategy.builders.strategy_builder import StrategyBuilder
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.strategy import Strategy


class _FakeLiveAnalyticsPort:
    def __init__(self, context: EvaluationContext | None = None, snapshot: LiveAnalyticsSnapshot | None = None) -> None:
        self.context = context
        self.snapshot = snapshot

    def get_chain(self, underlying, exchange, expiry_date):
        raise AssertionError("not exercised")

    def get_analytics(self, underlying, exchange, expiry_date):
        return self.snapshot

    def request_refresh(self, underlying, exchange, expiry_date):
        raise AssertionError("not exercised")

    def refresh_and_get_analytics(self, underlying, exchange, expiry_date):
        raise AssertionError("not exercised")

    def refresh_mode(self):
        raise AssertionError("not exercised")

    def build_evaluation_context(self, underlying, exchange, expiry_date):
        return self.context


class _FakePortfolioRepository:
    def __init__(self) -> None:
        self.saved: dict[str, object] = {}

    def get(self, portfolio_id: str):
        return self.saved.get(portfolio_id)


class _FakePortfolioService:
    def __init__(self) -> None:
        self.created: list[tuple[str, Decimal]] = []
        self.calculate_calls: list[str] = []
        self.repository = _FakePortfolioRepository()

    def create_portfolio(self, name: str, initial_cash: Decimal):
        self.created.append((name, initial_cash))
        portfolio = SimpleNamespace(portfolio_id="P1")
        self.repository.saved["P1"] = portfolio
        return portfolio

    def calculate(self, request):
        self.calculate_calls.append(request.portfolio_id)
        return SimpleNamespace(portfolio_value=Decimal("0"))


class _RecordingAIEngine:
    def __init__(self) -> None:
        self.received_requests: list = []

    def generate(self, request):
        self.received_requests.append(request)
        return SimpleNamespace(recommendations=(), primary=None)


class _FakePortfolioProvider:
    def __init__(self, service: _FakePortfolioService) -> None:
        self.service = service
        self.repository = service.repository


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


def _snapshot() -> LiveAnalyticsSnapshot:
    return LiveAnalyticsSnapshot(
        underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026",
        risk=SimpleNamespace(name="risk"), margin=SimpleNamespace(name="margin"),
        probability=SimpleNamespace(name="probability"), chain_analysis=SimpleNamespace(name="chain_analysis"),
        volatility=SimpleNamespace(name="volatility"),
        calculation_timestamp=datetime.now(timezone.utc),
    )


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


def _service_with_active_strategy(
    strategy: Strategy | None,
    live_analytics=None,
    ai_engine: _RecordingAIEngine | None = None,
    portfolio_service: _FakePortfolioService | None = None,
) -> tuple[AIWorkspaceService, str, _RecordingAIEngine, _FakePortfolioService]:
    sessions = SessionManager()
    cache = WorkspaceCache()
    session = sessions.create(WorkspaceType.TRADING)
    if strategy is not None:
        cache.put_strategy(strategy.strategy_id, strategy)
        sessions.set_active_workspace(session.session_id, WorkspaceType.TRADING, strategy.strategy_id)
    ai_engine = ai_engine or _RecordingAIEngine()
    portfolio_service = portfolio_service or _FakePortfolioService()
    engines = SimpleNamespace(
        ai=SimpleNamespace(service=ai_engine),
        portfolio=_FakePortfolioProvider(portfolio_service),
    )
    service = AIWorkspaceService(
        engines=engines, sessions=sessions, cache=cache, live_analytics=live_analytics or _FakeLiveAnalyticsPort(),
    )
    return service, session.session_id, ai_engine, portfolio_service


class TestGenerateRecommendationSuccess:
    def test_returns_success_with_batch(self) -> None:
        strategy = _strategy((_leg(),))
        service, session_id, _, _ = _service_with_active_strategy(strategy)

        result = service.generate_recommendation_for_active_strategy(session_id)

        assert result.success is True
        assert result.message == "0 recommendation(s) generated"

    def test_creates_a_fresh_portfolio_when_none_active(self) -> None:
        strategy = _strategy((_leg(),))
        service, session_id, _, portfolio_service = _service_with_active_strategy(strategy)

        service.generate_recommendation_for_active_strategy(session_id)

        assert len(portfolio_service.created) == 1
        assert portfolio_service.created[0][1] == Decimal("0")

    def test_reuses_existing_active_portfolio_without_recreating(self) -> None:
        strategy = _strategy((_leg(),))
        service, session_id, _, portfolio_service = _service_with_active_strategy(strategy)

        service.generate_recommendation_for_active_strategy(session_id)
        service.generate_recommendation_for_active_strategy(session_id)

        assert len(portfolio_service.created) == 1  # second call reuses the first portfolio

    def test_request_carries_real_portfolio_result(self) -> None:
        strategy = _strategy((_leg(),))
        service, session_id, ai_engine, _ = _service_with_active_strategy(strategy)

        service.generate_recommendation_for_active_strategy(session_id)

        request = ai_engine.received_requests[0]
        assert request.portfolio_result.portfolio_value == Decimal("0")
        assert request.session_id == session_id

    def test_request_carries_live_analytics_results_when_chain_subscribed(self) -> None:
        strategy = _strategy((_leg(),))
        snapshot = _snapshot()
        context = _context()
        port = _FakeLiveAnalyticsPort(context=context, snapshot=snapshot)
        service, session_id, ai_engine, _ = _service_with_active_strategy(strategy, live_analytics=port)

        service.generate_recommendation_for_active_strategy(session_id)

        request = ai_engine.received_requests[0]
        assert request.risk_result is snapshot.risk
        assert request.margin_result is snapshot.margin
        assert request.probability_result is snapshot.probability
        assert request.option_chain_analysis is snapshot.chain_analysis
        assert request.volatility_result is snapshot.volatility
        assert request.market_snapshot is context.market_snapshot

    def test_request_leaves_live_fields_none_when_chain_not_subscribed(self) -> None:
        strategy = _strategy((_leg(),))
        service, session_id, ai_engine, _ = _service_with_active_strategy(strategy)  # default port returns None

        service.generate_recommendation_for_active_strategy(session_id)

        request = ai_engine.received_requests[0]
        assert request.risk_result is None
        assert request.margin_result is None
        assert request.market_snapshot is None

    def test_request_carries_cached_optimization_result_when_present(self) -> None:
        strategy = _strategy((_leg(),))
        service, session_id, ai_engine, _ = _service_with_active_strategy(strategy)
        cached_optimization = SimpleNamespace(name="optimization")
        service._cache.put_data(f"{session_id}:optimization", cached_optimization)  # noqa: SLF001

        service.generate_recommendation_for_active_strategy(session_id)

        assert ai_engine.received_requests[0].optimization_result is cached_optimization


class TestGenerateRecommendationUnavailableFallsBackGracefully:
    def test_no_active_strategy_returns_failure_without_crashing(self) -> None:
        service, session_id, ai_engine, _ = _service_with_active_strategy(None)

        result = service.generate_recommendation_for_active_strategy(session_id)

        assert result.success is False
        assert result.message == "No active strategy to generate recommendations for"
        assert ai_engine.received_requests == []

    def test_strategy_with_no_legs_still_generates_using_portfolio_only(self) -> None:
        """No legs means no chain to pull live analytics from, but the
        request is still valid (portfolio_result is the only required
        field) -- this should not fail."""
        strategy = _strategy(())
        service, session_id, ai_engine, _ = _service_with_active_strategy(strategy)

        result = service.generate_recommendation_for_active_strategy(session_id)

        assert result.success is True
        assert len(ai_engine.received_requests) == 1
