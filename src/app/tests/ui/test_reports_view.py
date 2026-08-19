"""Tests for ReportsView: the report list table must actually render rows
from reports_changed, not just sit empty forever."""

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from app.ui.reports.reports_view import ReportsView


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


class _FakeCommand:
    def execute(self) -> None:
        pass


class _FakeReportsViewModel(QObject):
    reports_changed = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.refresh_command = _FakeCommand()
        self.export_command = _FakeCommand()


def _make_view(qapp: QApplication) -> tuple[ReportsView, _FakeReportsViewModel]:
    vm = _FakeReportsViewModel()
    return ReportsView(vm), vm


class TestReportsTable:
    def test_reports_changed_populates_rows(self, qapp: QApplication) -> None:
        view, vm = _make_view(qapp)

        vm.reports_changed.emit(["s1:portfolio-report", "s1:backtest-report"])

        assert view._table_model.rowCount() == 2
        assert view._table_model.item(0, 0).text() == "s1:portfolio-report"

    def test_empty_reports_clears_table(self, qapp: QApplication) -> None:
        view, vm = _make_view(qapp)
        vm.reports_changed.emit(["s1:portfolio-report"])

        vm.reports_changed.emit([])

        assert view._table_model.rowCount() == 0
