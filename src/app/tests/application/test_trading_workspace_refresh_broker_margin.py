"""Tests for TradingWorkspaceService.refresh_broker_margin(): the on-demand
entry point that re-evaluates a strategy with real broker margin when
available, falling back to the existing estimated-margin path otherwise.
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
from app.strategy.models.request import StrategyEvaluationRequest
from app.strategy.models.strategy import Strategy


def _request() -> StrategyEvaluationRequest:
    leg = StrategyLeg(
        leg_id="L1", kind=LegKind.CALL_SELL, quantity=75, premium=Decimal("100"),
        strike=Decimal("24500"), underlying="NIFTY", exchange="NFO",
    )
    strategy = Strategy(metadata=StrategyBuilder(name="Test").build().metadata, legs=(leg,))
    return StrategyEvaluationRequest(
        strategy=strategy,
        calculation_context=SimpleNamespace(),
        option_contract=SimpleNamespace(),
        option_chain=SimpleNamespace(),
        market_snapshot=SimpleNamespace(),
        chain_market_snapshot=SimpleNamespace(),
        volatility_market_snapshot=SimpleNamespace(),
        historical_data=SimpleNamespace(),
    )


class _RecordingEngines:
    """Fake EngineRegistry: only strategy.service.evaluate() is exercised by
    refresh_broker_margin(); records the request it received."""

    def __init__(self) -> None:
        self.received_requests: list[StrategyEvaluationRequest] = []
        strategy_service = SimpleNamespace(evaluate=self._evaluate)
        self.strategy = SimpleNamespace(service=strategy_service)

    def _evaluate(self, request: StrategyEvaluationRequest):
        self.received_requests.append(request)
        return SimpleNamespace(strategy=request.strategy, broker_response=request.broker_response)


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


def _service_with_session(
    engines: _RecordingEngines, broker_margin: _FakeBrokerMarginPort | None = None
) -> tuple[TradingWorkspaceService, str]:
    sessions = SessionManager()
    session = sessions.create(WorkspaceType.TRADING)
    service = TradingWorkspaceService(
        engines, sessions, WorkspaceCache(), broker_margin=broker_margin,
    )
    return service, session.session_id


class TestRefreshBrokerMarginWithRealBroker:
    def test_populates_broker_response_when_available(self) -> None:
        engines = _RecordingEngines()
        service, session_id = _service_with_session(
            engines, _FakeBrokerMarginPort(_broker_response())
        )
        request = _request()

        service.refresh_broker_margin(session_id, request, "NFO")

        assert len(engines.received_requests) == 1
        assert engines.received_requests[0].broker_response is not None
        assert engines.received_requests[0].broker_response.total_margin == Decimal("9000")

    def test_passes_strategy_legs_and_exchange_to_broker_margin_port(self) -> None:
        port = _FakeBrokerMarginPort(_broker_response())
        engines = _RecordingEngines()
        service, session_id = _service_with_session(engines, port)
        request = _request()

        service.refresh_broker_margin(session_id, request, "NFO")

        assert port.received_legs == request.strategy.legs
        assert port.received_exchange == "NFO"

    def test_original_request_object_is_not_mutated(self) -> None:
        """StrategyEvaluationRequest is frozen -- refresh_broker_margin must
        build a new request via replace(), never mutate the caller's."""
        engines = _RecordingEngines()
        service, session_id = _service_with_session(
            engines, _FakeBrokerMarginPort(_broker_response())
        )
        request = _request()
        assert request.broker_response is None

        service.refresh_broker_margin(session_id, request, "NFO")

        assert request.broker_response is None


class TestRefreshBrokerMarginFallsBackWhenUnavailable:
    def test_no_broker_margin_port_configured_falls_back_to_estimate(self) -> None:
        engines = _RecordingEngines()
        service, session_id = _service_with_session(engines, None)
        request = _request()

        service.refresh_broker_margin(session_id, request, "NFO")

        assert engines.received_requests[0].broker_response is None

    def test_broker_margin_port_returns_none_falls_back_to_estimate(self) -> None:
        engines = _RecordingEngines()
        service, session_id = _service_with_session(engines, _FakeBrokerMarginPort(None))
        request = _request()

        service.refresh_broker_margin(session_id, request, "NFO")

        assert engines.received_requests[0].broker_response is None

    def test_falls_back_call_still_evaluates_and_returns_result(self) -> None:
        engines = _RecordingEngines()
        service, session_id = _service_with_session(engines, _FakeBrokerMarginPort(None))
        request = _request()

        result = service.refresh_broker_margin(session_id, request, "NFO")

        assert result is not None
        assert result.strategy is request.strategy
