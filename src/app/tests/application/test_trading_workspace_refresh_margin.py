"""Tests for TradingWorkspaceService.refresh_margin(): looks up the active
strategy directly from session/cache state (no StrategyEvaluationRequest
needed) and returns real broker margin for it, for an on-demand "Refresh
Margin" UI action.
"""

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.services.trading_workspace_service import TradingWorkspaceService
from app.application.session.session_manager import SessionManager
from app.margin.models.broker_response import BrokerMarginResponse
from app.strategy.builders.strategy_builder import StrategyBuilder
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.strategy import Strategy


class _FakeBrokerMarginPort:
    def __init__(self, response: BrokerMarginResponse | None) -> None:
        self.response = response
        self.received_legs = None
        self.received_exchange = None

    def calculate_margin(self, legs, exchange):
        self.received_legs = legs
        self.received_exchange = exchange
        return self.response


def _broker_response() -> BrokerMarginResponse:
    return BrokerMarginResponse(
        broker_id="BREEZE", initial_margin=Decimal("9000"), exposure_margin=Decimal("2000"),
        span_margin=Decimal("7000"), total_margin=Decimal("9000"),
        available_margin=Decimal("41000"), account_balance=Decimal("100000"),
        captured_at=datetime.now(timezone.utc),
    )


def _strategy_with_leg() -> Strategy:
    leg = StrategyLeg(
        leg_id="L1", kind=LegKind.CALL_SELL, quantity=75, premium=Decimal("100"),
        strike=Decimal("24500"), underlying="NIFTY", exchange="NFO",
    )
    return Strategy(metadata=StrategyBuilder(name="Test").build().metadata, legs=(leg,))


def _service(broker_margin=None) -> tuple[TradingWorkspaceService, SessionManager, WorkspaceCache]:
    sessions = SessionManager()
    cache = WorkspaceCache()
    service = TradingWorkspaceService(
        SimpleNamespace(), sessions, cache, broker_margin=broker_margin,
    )
    return service, sessions, cache


class TestRefreshMarginNoActiveStrategy:
    def test_no_workspace_entity_returns_failure_without_crashing(self) -> None:
        service, sessions, cache = _service(_FakeBrokerMarginPort(_broker_response()))
        session = sessions.create(WorkspaceType.TRADING)

        result = service.refresh_margin(session.session_id, "NFO")

        assert result.success is False
        assert result.message == "No active strategy to refresh margin for"

    def test_entity_id_set_but_strategy_missing_from_cache(self) -> None:
        service, sessions, cache = _service(_FakeBrokerMarginPort(_broker_response()))
        session = sessions.create(WorkspaceType.TRADING)
        sessions.set_active_workspace(session.session_id, WorkspaceType.TRADING, "ghost-id")

        result = service.refresh_margin(session.session_id, "NFO")

        assert result.success is False
        assert result.message == "Strategy not found: ghost-id"


class TestRefreshMarginWithActiveStrategy:
    def _active_session(self, service, sessions, cache):
        strategy = _strategy_with_leg()
        cache.put_strategy(strategy.strategy_id, strategy)
        session = sessions.create(WorkspaceType.TRADING)
        sessions.set_active_workspace(session.session_id, WorkspaceType.TRADING, strategy.strategy_id)
        return session.session_id, strategy

    def test_returns_real_broker_margin_when_available(self) -> None:
        port = _FakeBrokerMarginPort(_broker_response())
        service, sessions, cache = _service(port)
        session_id, strategy = self._active_session(service, sessions, cache)

        result = service.refresh_margin(session_id, "NFO")

        assert result.success is True
        assert result.message == "Broker margin refreshed"
        assert result.data.total_margin == Decimal("9000")
        assert port.received_legs == strategy.legs
        assert port.received_exchange == "NFO"

    def test_broker_margin_unavailable_returns_failure_not_crash(self) -> None:
        service, sessions, cache = _service(_FakeBrokerMarginPort(None))
        session_id, _ = self._active_session(service, sessions, cache)

        result = service.refresh_margin(session_id, "NFO")

        assert result.success is False
        assert result.message == "Broker margin unavailable — showing estimate"

    def test_no_broker_margin_port_configured_returns_failure_not_crash(self) -> None:
        service, sessions, cache = _service(broker_margin=None)
        session_id, _ = self._active_session(service, sessions, cache)

        result = service.refresh_margin(session_id, "NFO")

        assert result.success is False
        assert result.message == "Broker margin unavailable — showing estimate"

    def test_defaults_to_nfo_exchange_when_not_specified(self) -> None:
        port = _FakeBrokerMarginPort(_broker_response())
        service, sessions, cache = _service(port)
        session_id, _ = self._active_session(service, sessions, cache)

        service.refresh_margin(session_id)

        assert port.received_exchange == "NFO"
