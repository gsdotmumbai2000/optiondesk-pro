"""Tests for BacktestingWorkspaceService.run_active_strategy_backtest(): the
on-demand "Run" action that backtests whatever strategy is currently active
in Trading/Strategy workspace against real broker historical bars.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.services.backtesting_workspace_service import BacktestingWorkspaceService
from app.application.session.session_manager import SessionManager
from app.backtesting.models.historical import HistoricalMarketData
from app.backtesting.models.request import BacktestRequest
from app.market_data.models.snapshot import HistoricalBar
from app.strategy.builders.strategy_builder import StrategyBuilder
from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.strategy import Strategy


class _FakeBrokerHistoricalPort:
    def __init__(self, market_data: HistoricalMarketData | None) -> None:
        self.market_data = market_data
        self.received: tuple[str, str, datetime, datetime] | None = None

    def get_historical_bars(self, underlying, exchange, from_date, to_date):
        self.received = (underlying, exchange, from_date, to_date)
        return self.market_data


class _RecordingBacktestEngineService:
    """Fake engines.backtest.service: only run() is exercised."""

    def __init__(self) -> None:
        self.received_requests: list[BacktestRequest] = []

    def run(self, request: BacktestRequest):
        self.received_requests.append(request)
        from app.backtesting.models.trades import EquityCurve
        from types import SimpleNamespace

        return SimpleNamespace(equity_curve=EquityCurve(points=()), total_trades=0)


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


def _market_data(underlying: str = "NIFTY") -> HistoricalMarketData:
    bar = HistoricalBar(
        symbol=underlying, exchange="NFO", timestamp=datetime(2026, 8, 1, tzinfo=timezone.utc),
        open=Decimal("24000"), high=Decimal("24200"), low=Decimal("23900"), close=Decimal("24100"),
    )
    return HistoricalMarketData(underlying=underlying, exchange="NFO", bars=(bar,))


def _service_with_active_strategy(
    broker_historical, strategy: Strategy | None, *, workspace: WorkspaceType = WorkspaceType.TRADING,
) -> tuple[BacktestingWorkspaceService, str, _RecordingBacktestEngineService]:
    from types import SimpleNamespace

    sessions = SessionManager()
    cache = WorkspaceCache()
    session = sessions.create(WorkspaceType.TRADING)
    if strategy is not None:
        cache.put_strategy(strategy.strategy_id, strategy)
        sessions.set_active_workspace(session.session_id, workspace, strategy.strategy_id)
    backtest_service = _RecordingBacktestEngineService()
    engines = SimpleNamespace(backtest=SimpleNamespace(service=backtest_service))
    service = BacktestingWorkspaceService(engines, sessions, cache, broker_historical)
    return service, session.session_id, backtest_service


class TestRunActiveStrategyBacktestSuccess:
    def test_returns_result_on_success(self) -> None:
        strategy = _strategy((_leg(),))
        port = _FakeBrokerHistoricalPort(_market_data())
        service, session_id, engine = _service_with_active_strategy(port, strategy)

        result = service.run_active_strategy_backtest(session_id)

        assert result.success is True
        assert result.message == "Backtest complete"
        assert result.data is not None
        assert len(engine.received_requests) == 1

    def test_active_strategy_from_strategy_workspace_is_used_too(self) -> None:
        """A strategy built/saved from the Strategy Builder without ever
        being loaded into Trading is still backtestable."""
        strategy = _strategy((_leg(),))
        port = _FakeBrokerHistoricalPort(_market_data())
        service, session_id, engine = _service_with_active_strategy(
            port, strategy, workspace=WorkspaceType.STRATEGY,
        )

        result = service.run_active_strategy_backtest(session_id)

        assert result.success is True

    def test_derives_underlying_and_exchange_from_first_leg(self) -> None:
        strategy = _strategy((_leg(underlying="BANKNIFTY", exchange="NFO"),))
        port = _FakeBrokerHistoricalPort(_market_data("BANKNIFTY"))
        service, session_id, _ = _service_with_active_strategy(port, strategy)

        service.run_active_strategy_backtest(session_id)

        assert port.received is not None
        assert port.received[0] == "BANKNIFTY"
        assert port.received[1] == "NFO"

    def test_request_uses_real_strategy_and_market_data_no_placeholders(self) -> None:
        strategy = _strategy((_leg(),))
        market_data = _market_data()
        port = _FakeBrokerHistoricalPort(market_data)
        service, session_id, engine = _service_with_active_strategy(port, strategy)

        service.run_active_strategy_backtest(session_id)

        request = engine.received_requests[0]
        assert request.strategy is strategy
        assert request.market_data is market_data
        assert request.parameters.initial_capital > 0


class TestRunActiveStrategyBacktestUnavailableFallsBackGracefully:
    def test_no_active_strategy_returns_failure_without_crashing(self) -> None:
        service, session_id, _ = _service_with_active_strategy(_FakeBrokerHistoricalPort(_market_data()), None)

        result = service.run_active_strategy_backtest(session_id)

        assert result.success is False
        assert result.message == "No active strategy to backtest"

    def test_strategy_with_no_legs_returns_failure(self) -> None:
        strategy = _strategy(())
        service, session_id, _ = _service_with_active_strategy(_FakeBrokerHistoricalPort(_market_data()), strategy)

        result = service.run_active_strategy_backtest(session_id)

        assert result.success is False
        assert result.message == "Strategy has no legs to backtest"

    def test_no_broker_historical_port_configured_returns_failure(self) -> None:
        strategy = _strategy((_leg(),))
        service, session_id, _ = _service_with_active_strategy(None, strategy)

        result = service.run_active_strategy_backtest(session_id)

        assert result.success is False
        assert result.message == "No broker historical data source configured"

    def test_no_bars_returned_returns_failure(self) -> None:
        strategy = _strategy((_leg(),))
        port = _FakeBrokerHistoricalPort(None)  # simulates disconnected/failed fetch
        service, session_id, _ = _service_with_active_strategy(port, strategy)

        result = service.run_active_strategy_backtest(session_id)

        assert result.success is False
        assert "Historical data unavailable" in result.message

    def test_empty_bars_tuple_returns_failure(self) -> None:
        strategy = _strategy((_leg(),))
        empty = HistoricalMarketData(underlying="NIFTY", exchange="NFO", bars=())
        port = _FakeBrokerHistoricalPort(empty)
        service, session_id, _ = _service_with_active_strategy(port, strategy)

        result = service.run_active_strategy_backtest(session_id)

        assert result.success is False
        assert "Historical data unavailable" in result.message
