"""Tests for TradingWorkspaceService.evaluate_active_strategy(): the
on-demand "Evaluate" action that recomputes payoff/Greeks for whatever
strategy is currently loaded into this session's Trading workspace, sourced
from a synchronous live-analytics refresh of that strategy's chain.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.services.trading_workspace_service import TradingWorkspaceService
from app.application.session.session_manager import SessionManager
from app.live.models.analytics import LiveAnalyticsSnapshot
from app.strategy.builders.strategy_builder import StrategyBuilder
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.strategy import Strategy


class _FakeLiveAnalyticsPort:
    """Test double for LiveAnalyticsPort: only refresh_and_get_analytics()
    is exercised by evaluate_active_strategy()."""

    def __init__(self, snapshot: LiveAnalyticsSnapshot | None) -> None:
        self.snapshot = snapshot
        self.received: tuple[str, str, str] | None = None

    def get_chain(self, underlying, exchange, expiry_date):
        raise AssertionError("not exercised by evaluate_active_strategy()")

    def get_analytics(self, underlying, exchange, expiry_date):
        raise AssertionError("not exercised by evaluate_active_strategy()")

    def request_refresh(self, underlying, exchange, expiry_date):
        raise AssertionError("not exercised by evaluate_active_strategy()")

    def refresh_mode(self):
        raise AssertionError("not exercised by evaluate_active_strategy()")

    def refresh_and_get_analytics(self, underlying: str, exchange: str, expiry_date: str):
        self.received = (underlying, exchange, expiry_date)
        return self.snapshot


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
        calculation_timestamp=datetime.now(timezone.utc),
    )


def _service_with_active_strategy(
    live_analytics, strategy: Strategy | None,
) -> tuple[TradingWorkspaceService, str]:
    sessions = SessionManager()
    cache = WorkspaceCache()
    session = sessions.create(WorkspaceType.TRADING)
    if strategy is not None:
        cache.put_strategy(strategy.strategy_id, strategy)
        sessions.set_active_workspace(session.session_id, WorkspaceType.TRADING, strategy.strategy_id)
    service = TradingWorkspaceService(
        engines=None, sessions=sessions, cache=cache, live_analytics=live_analytics,
    )
    return service, session.session_id


class TestEvaluateActiveStrategySuccess:
    def test_returns_snapshot_on_success(self) -> None:
        snapshot = _snapshot()
        port = _FakeLiveAnalyticsPort(snapshot)
        strategy = _strategy((_leg(),))
        service, session_id = _service_with_active_strategy(port, strategy)

        result = service.evaluate_active_strategy(session_id)

        assert result.success is True
        assert result.data is snapshot
        assert result.message == "Strategy evaluated"

    def test_derives_chain_key_from_first_leg(self) -> None:
        port = _FakeLiveAnalyticsPort(_snapshot())
        strategy = _strategy((_leg(underlying="BANKNIFTY", exchange="NFO", expiry=date(2026, 9, 24)),))
        service, session_id = _service_with_active_strategy(port, strategy)

        service.evaluate_active_strategy(session_id)

        assert port.received == ("BANKNIFTY", "NFO", "24-Sep-2026")


class TestEvaluateActiveStrategyUnavailableFallsBackGracefully:
    def test_no_active_strategy_returns_failure_without_crashing(self) -> None:
        service, session_id = _service_with_active_strategy(_FakeLiveAnalyticsPort(_snapshot()), None)

        result = service.evaluate_active_strategy(session_id)

        assert result.success is False
        assert result.message == "No active strategy to evaluate"
        assert result.data is None

    def test_strategy_with_no_legs_returns_failure(self) -> None:
        port = _FakeLiveAnalyticsPort(_snapshot())
        strategy = _strategy(())
        service, session_id = _service_with_active_strategy(port, strategy)

        result = service.evaluate_active_strategy(session_id)

        assert result.success is False
        assert result.message == "Strategy has no legs to evaluate"

    def test_leg_missing_expiry_returns_failure(self) -> None:
        port = _FakeLiveAnalyticsPort(_snapshot())
        strategy = _strategy((_leg(expiry=None),))
        service, session_id = _service_with_active_strategy(port, strategy)

        result = service.evaluate_active_strategy(session_id)

        assert result.success is False
        assert result.message == "Strategy legs are missing underlying/expiry"

    def test_chain_unavailable_returns_failure_without_crashing(self) -> None:
        port = _FakeLiveAnalyticsPort(None)  # simulates an unsubscribed chain
        strategy = _strategy((_leg(),))
        service, session_id = _service_with_active_strategy(port, strategy)

        result = service.evaluate_active_strategy(session_id)

        assert result.success is False
        assert "Live chain unavailable" in result.message

    def test_no_live_analytics_port_configured_returns_failure(self) -> None:
        strategy = _strategy((_leg(),))
        sessions = SessionManager()
        cache = WorkspaceCache()
        session = sessions.create(WorkspaceType.TRADING)
        cache.put_strategy(strategy.strategy_id, strategy)
        sessions.set_active_workspace(session.session_id, WorkspaceType.TRADING, strategy.strategy_id)
        service = TradingWorkspaceService(engines=None, sessions=sessions, cache=cache)

        result = service.evaluate_active_strategy(session.session_id)

        assert result.success is False
        assert "Live chain unavailable" in result.message
