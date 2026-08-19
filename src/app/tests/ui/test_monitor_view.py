"""Tests for MonitorView: alerts/warnings/recommendations tables must
actually render rows, not just sit empty or update a tooltip."""

from dataclasses import dataclass
from decimal import Decimal
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter

from app.ui.monitor.monitor_view import MonitorView


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


@dataclass(frozen=True, slots=True)
class _Alert:
    priority: SimpleNamespace
    title: str
    symbol: str
    message: str
    raised_at: str


@dataclass(frozen=True, slots=True)
class _Recommendation:
    recommendation_type: SimpleNamespace
    symbol: str
    title: str
    suggested_action: str
    confidence: Decimal


def _alert(symbol: str = "NIFTY") -> _Alert:
    return _Alert(
        priority=SimpleNamespace(value="CRITICAL"), title="Margin breach", symbol=symbol,
        message="Margin utilization above threshold", raised_at="2026-08-19T10:00:00",
    )


def _recommendation(symbol: str = "NIFTY") -> _Recommendation:
    return _Recommendation(
        recommendation_type=SimpleNamespace(value="ADJUST"), symbol=symbol, title="Roll strike",
        suggested_action="Roll short call up 200 points", confidence=Decimal("0.8"),
    )


class _FakeMonitorViewModel(QObject):
    alerts_changed = Signal(list)
    warnings_changed = Signal(list)
    recommendations_changed = Signal(list)


def _make_view(qapp: QApplication) -> tuple[MonitorView, _FakeMonitorViewModel]:
    vm = _FakeMonitorViewModel()
    return MonitorView(vm), vm


class TestAlertsTable:
    def test_alerts_changed_populates_rows(self, qapp: QApplication) -> None:
        view, vm = _make_view(qapp)

        vm.alerts_changed.emit([_alert("A"), _alert("B")])

        assert view._alerts_model.rowCount() == 2
        assert view._alerts_model.item(0, 2).text() == "A"

    def test_empty_alerts_clears_table(self, qapp: QApplication) -> None:
        view, vm = _make_view(qapp)
        vm.alerts_changed.emit([_alert()])

        vm.alerts_changed.emit([])

        assert view._alerts_model.rowCount() == 0


class TestWarningsTable:
    def test_warnings_changed_populates_rows_independently_of_alerts(self, qapp: QApplication) -> None:
        view, vm = _make_view(qapp)

        vm.alerts_changed.emit([_alert("A")])
        vm.warnings_changed.emit([_alert("B"), _alert("C")])

        assert view._alerts_model.rowCount() == 1
        assert view._warnings_model.rowCount() == 2


class TestRecommendationsTable:
    def test_recommendations_changed_populates_rows(self, qapp: QApplication) -> None:
        view, vm = _make_view(qapp)

        vm.recommendations_changed.emit([_recommendation("A")])

        assert view._recs_model.rowCount() == 1
        row = [view._recs_model.item(0, c).text() for c in range(5)]
        assert row == ["ADJUST", "A", "Roll strike", "Roll short call up 200 points", "0.8"]


class TestTablesAreIndependentlyVerticallyResizable:
    """Each of the three tables sits in its own QSplitter pane, so dragging
    the handle between any two must resize just that pair, not force all
    three to share space in a fixed proportion."""

    def test_alerts_warnings_recommendations_are_three_splitter_panes(self, qapp: QApplication) -> None:
        view, _vm = _make_view(qapp)

        splitters = view.findChildren(QSplitter)

        assert len(splitters) == 1
        assert splitters[0].count() == 3

    def test_dragging_the_handle_resizes_one_table_without_touching_the_others(
        self, qapp: QApplication,
    ) -> None:
        view, _vm = _make_view(qapp)
        window = QMainWindow()
        window.setCentralWidget(view)
        window.resize(600, 900)
        window.show()
        qapp.processEvents()
        splitter = view.findChildren(QSplitter)[0]
        recommendations_height_before = view._recs.height()

        sizes = splitter.sizes()
        sizes = [sizes[0] + 200, max(sizes[1] - 200, 20), sizes[2]]
        splitter.setSizes(sizes)
        qapp.processEvents()

        window.close()
        assert view._alerts.height() > view._warnings.height()
        assert view._recs.height() == pytest.approx(recommendations_height_before, abs=2)
