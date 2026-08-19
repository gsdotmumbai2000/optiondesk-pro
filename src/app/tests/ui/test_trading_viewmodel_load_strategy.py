"""Tests for TradingViewModel.list_strategies()/load_strategy(): the real
flow behind the Strategy Builder's "Load" button and the ribbon's "Open"
button -- picks a saved strategy and loads its legs into the builder,
marking it active in both the Strategy and Trading workspaces so
Evaluate/Optimize/Paper Trade/Refresh Margin can find it afterward.
"""

from dataclasses import dataclass
from decimal import Decimal
from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult
from app.strategy.models.enums import LegKind, StrategyType
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.metadata import StrategyMetadata
from app.strategy.models.strategy import Strategy
from app.ui.viewmodels.context import ViewModelContext
from app.ui.viewmodels.trading_viewmodel import TradingViewModel


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _strategy(strategy_id: str = "strat-1", name: str = "Bull Call Spread") -> Strategy:
    leg = StrategyLeg(
        leg_id="L1", kind=LegKind.CALL_BUY, quantity=1, premium=Decimal("100"), strike=Decimal("24500"),
    )
    metadata = StrategyMetadata(strategy_id=strategy_id, name=name, recognized_type=StrategyType.CUSTOM)
    return Strategy(metadata=metadata, legs=(leg,))


class _FakeStrategyService:
    def __init__(
        self, load_result: WorkspaceOperationResult, list_result: WorkspaceOperationResult | None = None,
    ) -> None:
        self._load_result = load_result
        self._list_result = list_result
        self.load_calls: list[tuple[str, str]] = []
        self.list_calls: list[str] = []

    def load_strategy(self, session_id: str, strategy_id: str) -> WorkspaceOperationResult:
        self.load_calls.append((session_id, strategy_id))
        return self._load_result

    def list_strategies(self, session_id: str) -> WorkspaceOperationResult:
        self.list_calls.append(session_id)
        return self._list_result


class _FakeTradingService:
    def __init__(self, load_result: WorkspaceOperationResult) -> None:
        self._load_result = load_result
        self.load_calls: list[tuple[str, str]] = []

    def load_strategy(self, session_id: str, strategy_id: str) -> WorkspaceOperationResult:
        self.load_calls.append((session_id, strategy_id))
        return self._load_result


def _make_viewmodel(
    strategy_load_result: WorkspaceOperationResult,
    trading_load_result: WorkspaceOperationResult | None = None,
    list_result: WorkspaceOperationResult | None = None,
) -> tuple[TradingViewModel, _FakeStrategyService, _FakeTradingService]:
    strategy_service = _FakeStrategyService(strategy_load_result, list_result)
    trading_service = _FakeTradingService(trading_load_result or strategy_load_result)
    provider = SimpleNamespace(strategy=strategy_service, trading=trading_service)
    ctx = ViewModelContext(provider=provider, worker=SimpleNamespace(), events=SimpleNamespace(), session_id="s1")
    return TradingViewModel(ctx), strategy_service, trading_service


class TestListStrategies:
    def test_returns_id_name_pairs_from_the_repository(self, qapp: QApplication) -> None:
        list_result = WorkspaceOperationResult(
            True, WorkspaceType.STRATEGY, "2 strategies", [_strategy("a", "Iron Condor"), _strategy("b", "Straddle")],
        )
        vm, service, _trading = _make_viewmodel(
            WorkspaceOperationResult(True, WorkspaceType.STRATEGY, "Strategy loaded"), list_result=list_result,
        )

        pairs = vm.list_strategies()

        assert pairs == [("a", "Iron Condor"), ("b", "Straddle")]
        assert service.list_calls == ["s1"]

    def test_failure_returns_empty_list(self, qapp: QApplication) -> None:
        list_result = WorkspaceOperationResult(False, WorkspaceType.STRATEGY, "error")
        vm, _service, _trading = _make_viewmodel(
            WorkspaceOperationResult(True, WorkspaceType.STRATEGY, "Strategy loaded"), list_result=list_result,
        )

        assert vm.list_strategies() == []


class TestLoadStrategySuccess:
    def test_populates_builder_legs_from_the_loaded_strategy(self, qapp: QApplication) -> None:
        strategy = _strategy("strat-1")
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy loaded", strategy)
        vm, strategy_service, trading_service = _make_viewmodel(result)
        seen: list[list] = []
        vm.pending_legs_changed.connect(seen.append)

        vm.load_strategy("strat-1")

        assert seen == [list(strategy.legs)]
        assert strategy_service.load_calls == [("s1", "strat-1")]
        assert trading_service.load_calls == [("s1", "strat-1")]

    def test_updates_strategy_name(self, qapp: QApplication) -> None:
        strategy = _strategy("strat-1", name="Iron Condor")
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy loaded", strategy)
        vm, *_ = _make_viewmodel(result)
        seen: list[str] = []
        vm.strategy_name_changed.connect(seen.append)

        vm.load_strategy("strat-1")

        assert seen == ["Iron Condor"]
        assert vm.strategy_name == "Iron Condor"

    def test_status_message_reflects_trading_result(self, qapp: QApplication) -> None:
        strategy = _strategy("strat-1")
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy loaded", strategy)
        vm, *_ = _make_viewmodel(result)

        vm.load_strategy("strat-1")

        assert vm.status_message == "Strategy loaded"


class TestLoadStrategyFailure:
    def test_empty_strategy_id_does_not_call_either_service(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.TRADING, "Strategy loaded", _strategy())
        vm, strategy_service, trading_service = _make_viewmodel(result)

        vm.load_strategy("")

        assert vm.status_message == "No strategy selected"
        assert strategy_service.load_calls == []
        assert trading_service.load_calls == []

    def test_strategy_not_found_stops_before_touching_trading(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(False, WorkspaceType.STRATEGY, "Strategy not found: strat-1")
        vm, _strategy_service, trading_service = _make_viewmodel(result)
        seen: list[list] = []
        vm.pending_legs_changed.connect(seen.append)

        vm.load_strategy("strat-1")

        assert vm.status_message == "Strategy not found: strat-1"
        assert trading_service.load_calls == []
        assert seen == []

    def test_trading_load_failure_does_not_populate_builder(self, qapp: QApplication) -> None:
        strategy_result = WorkspaceOperationResult(True, WorkspaceType.STRATEGY, "Strategy loaded", _strategy())
        trading_result = WorkspaceOperationResult(False, WorkspaceType.TRADING, "Strategy not found: strat-1")
        vm, *_ = _make_viewmodel(strategy_result, trading_result)
        seen: list[list] = []
        vm.pending_legs_changed.connect(seen.append)

        vm.load_strategy("strat-1")

        assert vm.status_message == "Strategy not found: strat-1"
        assert seen == []
