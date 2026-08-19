"""Tests for the Strategy tab's list model and row-selection-driven Open
button: previously the table had no model at all (StrategyListView only set
a tooltip) and "Open" was a stub that never read a selection.
"""

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from app.strategy.models.enums import LegKind, StrategyType
from app.strategy.models.leg import StrategyLeg
from app.strategy.models.metadata import StrategyMetadata
from app.strategy.models.strategy import Strategy
from app.ui.strategy.strategy_list_model import COLUMNS, StrategyListTableModel
from app.ui.strategy.strategy_list_view import StrategyListView
from app.ui.viewmodels.context import ViewModelContext
from app.ui.viewmodels.strategy_viewmodel import StrategyViewModel


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _strategy(strategy_id: str, name: str) -> Strategy:
    return Strategy(
        metadata=StrategyMetadata(
            strategy_id=strategy_id,
            name=name,
            recognized_type=StrategyType.LONG_CALL,
            updated_at=datetime(2026, 8, 16, 10, 30, tzinfo=timezone.utc),
        ),
        legs=(
            StrategyLeg(
                leg_id="leg-1", kind=LegKind.CALL_BUY, quantity=50,
                premium=Decimal("120.5"), strike=Decimal("24500"),
            ),
        ),
    )


class TestStrategyListTableModel:
    def test_renders_name_type_legs_updated(self, qapp: QApplication) -> None:
        model = StrategyListTableModel()

        model.set_strategies([_strategy("strat-1", "Iron Condor")])

        assert model.rowCount() == 1
        assert model.columnCount() == len(COLUMNS)
        assert model.data(model.index(0, 0)) == "Iron Condor"
        assert model.data(model.index(0, 1)) == "LONG_CALL"
        assert model.data(model.index(0, 2)) == "1"
        assert model.data(model.index(0, 3)) == "2026-08-16 10:30"

    def test_maps_row_back_to_strategy_id(self, qapp: QApplication) -> None:
        model = StrategyListTableModel()

        model.set_strategies([_strategy("strat-1", "A"), _strategy("strat-2", "B")])

        assert model.strategy_id_for_row(0) == "strat-1"
        assert model.strategy_id_for_row(1) == "strat-2"

    def test_out_of_range_row_returns_empty_string(self, qapp: QApplication) -> None:
        model = StrategyListTableModel()
        model.set_strategies([_strategy("strat-1", "A")])

        assert model.strategy_id_for_row(5) == ""


class TestStrategyListViewOpenButton:
    def _make_view(self) -> tuple[StrategyListView, list[str]]:
        provider = SimpleNamespace()
        events = SimpleNamespace(strategy_updated=SimpleNamespace(connect=lambda *a, **k: None))
        ctx = ViewModelContext(provider=provider, worker=SimpleNamespace(), events=events, session_id="s1")
        vm = StrategyViewModel(ctx)
        opened: list[str] = []
        vm.open_strategy = opened.append  # type: ignore[method-assign]
        view = StrategyListView(vm)
        view._model.set_strategies([_strategy("strat-1", "A"), _strategy("strat-2", "B")])
        return view, opened

    def test_no_selection_falls_back_to_placeholder_status(self, qapp: QApplication) -> None:
        view, opened = self._make_view()

        view._open_selected_row()

        assert opened == []
        assert view._vm.status_message == "Select strategy to open"

    def test_selected_row_opens_its_strategy_id(self, qapp: QApplication) -> None:
        view, opened = self._make_view()
        view._table.selectRow(1)

        view._open_selected_row()

        assert opened == ["strat-2"]
