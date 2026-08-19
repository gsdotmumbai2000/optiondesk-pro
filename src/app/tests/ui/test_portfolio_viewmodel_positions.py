"""Tests for PortfolioViewModel positions/holdings plumbing: load_portfolio()
and refresh() must actually populate the positions/holdings lists from the
real Portfolio aggregate returned by the provider, not just update the
summary text.
"""

from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult
from app.ui.viewmodels.context import ViewModelContext
from app.ui.viewmodels.portfolio_viewmodel import PortfolioViewModel


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _portfolio(portfolio_id: str = "p1") -> SimpleNamespace:
    return SimpleNamespace(
        portfolio_id=portfolio_id,
        open_positions=["pos-a", "pos-b"],
        holdings=["hold-a"],
    )


class _FakePortfolioService:
    def __init__(self, load_result: WorkspaceOperationResult, view: SimpleNamespace | None = None) -> None:
        self._load_result = load_result
        self._view = view or SimpleNamespace(summary="Portfolio: none", entity_id="")
        self.load_calls: list[tuple[str, str]] = []

    def load_portfolio(self, session_id: str, portfolio_id: str) -> WorkspaceOperationResult:
        self.load_calls.append((session_id, portfolio_id))
        return self._load_result

    def view(self, session_id: str) -> SimpleNamespace:
        return self._view


class _FakeCoordinator:
    def __init__(self) -> None:
        self.notified: list[str] = []

    def notify_portfolio_loaded(self, portfolio_id: str) -> None:
        self.notified.append(portfolio_id)


def _make_viewmodel(
    load_result: WorkspaceOperationResult, view: SimpleNamespace | None = None,
) -> tuple[PortfolioViewModel, _FakePortfolioService]:
    service = _FakePortfolioService(load_result, view)
    provider = SimpleNamespace(portfolio=service, coordinator=_FakeCoordinator())
    events = SimpleNamespace(portfolio_updated=SimpleNamespace(connect=lambda *a, **k: None))
    ctx = ViewModelContext(provider=provider, worker=SimpleNamespace(), events=events, session_id="s1")
    return PortfolioViewModel(ctx), service


class TestLoadPortfolioPopulatesPositionsAndHoldings:
    def test_success_populates_both_lists(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.PORTFOLIO, "Portfolio loaded", _portfolio())
        vm, _service = _make_viewmodel(result)

        vm.load_portfolio("p1")

        assert vm.positions == ["pos-a", "pos-b"]
        assert vm.holdings == ["hold-a"]

    def test_failure_leaves_positions_and_holdings_empty(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(False, WorkspaceType.PORTFOLIO, "Portfolio not found: p1")
        vm, _service = _make_viewmodel(result)

        vm.load_portfolio("p1")

        assert vm.positions == []
        assert vm.holdings == []

    def test_emits_positions_and_holdings_changed(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.PORTFOLIO, "Portfolio loaded", _portfolio())
        vm, _service = _make_viewmodel(result)
        positions_seen: list[list] = []
        holdings_seen: list[list] = []
        vm.positions_changed.connect(positions_seen.append)
        vm.holdings_changed.connect(holdings_seen.append)

        vm.load_portfolio("p1")

        assert positions_seen == [["pos-a", "pos-b"]]
        assert holdings_seen == [["hold-a"]]


class TestRefreshRepopulatesWhenAPortfolioIsActive:
    def test_no_active_portfolio_does_not_call_load_portfolio(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.PORTFOLIO, "Portfolio loaded", _portfolio())
        view = SimpleNamespace(summary="Portfolio: none", entity_id="")
        vm, service = _make_viewmodel(result, view)

        vm.refresh()

        assert service.load_calls == []
        assert vm.positions == []

    def test_active_portfolio_repopulates_positions_and_holdings(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.PORTFOLIO, "Portfolio loaded", _portfolio("p1"))
        view = SimpleNamespace(summary="Portfolio: p1", entity_id="p1")
        vm, service = _make_viewmodel(result, view)

        vm.refresh()

        assert service.load_calls == [("s1", "p1")]
        assert vm.positions == ["pos-a", "pos-b"]

    def test_refresh_does_not_notify_coordinator(self, qapp: QApplication) -> None:
        """Routine refresh must not re-fire the portfolio-loaded coordinator
        event -- only the explicit load_portfolio() action should."""
        result = WorkspaceOperationResult(True, WorkspaceType.PORTFOLIO, "Portfolio loaded", _portfolio("p1"))
        view = SimpleNamespace(summary="Portfolio: p1", entity_id="p1")
        vm, service = _make_viewmodel(result, view)
        coordinator = vm._ctx.provider.coordinator

        vm.refresh()

        assert coordinator.notified == []
