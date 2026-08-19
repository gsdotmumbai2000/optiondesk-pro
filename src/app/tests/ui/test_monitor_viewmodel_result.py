"""Tests for MonitorViewModel.refresh_from_monitor_result(): must populate
alerts, warnings, and recommendations independently from the three separate
MonitorResult fields, not just open_alerts."""

from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from app.ui.viewmodels.context import ViewModelContext
from app.ui.viewmodels.monitor_viewmodel import MonitorViewModel


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _make_viewmodel() -> MonitorViewModel:
    events = SimpleNamespace(alert_raised=SimpleNamespace(connect=lambda *a, **k: None))
    ctx = ViewModelContext(provider=SimpleNamespace(), worker=SimpleNamespace(), events=events, session_id="s1")
    return MonitorViewModel(ctx)


def _monitor_result(open_alerts=(), warning_alerts=(), recommendation_list=()) -> SimpleNamespace:
    return SimpleNamespace(
        open_alerts=open_alerts, warning_alerts=warning_alerts, recommendation_list=recommendation_list,
    )


class TestRefreshFromMonitorResult:
    def test_populates_all_three_lists_independently(self, qapp: QApplication) -> None:
        vm = _make_viewmodel()
        result = _monitor_result(
            open_alerts=["alert-a"], warning_alerts=["warn-a", "warn-b"], recommendation_list=["rec-a"],
        )

        vm.refresh_from_monitor_result(result)

        assert vm.alerts == ["alert-a"]
        assert vm.warnings == ["warn-a", "warn-b"]
        assert vm.recommendations == ["rec-a"]

    def test_emits_all_three_changed_signals(self, qapp: QApplication) -> None:
        vm = _make_viewmodel()
        seen = {"alerts": [], "warnings": [], "recommendations": []}
        vm.alerts_changed.connect(seen["alerts"].append)
        vm.warnings_changed.connect(seen["warnings"].append)
        vm.recommendations_changed.connect(seen["recommendations"].append)
        result = _monitor_result(open_alerts=["a"], warning_alerts=["w"], recommendation_list=["r"])

        vm.refresh_from_monitor_result(result)

        assert seen == {"alerts": [["a"]], "warnings": [["w"]], "recommendations": [["r"]]}

    def test_none_result_leaves_lists_unchanged(self, qapp: QApplication) -> None:
        vm = _make_viewmodel()
        vm.refresh_from_monitor_result(_monitor_result(open_alerts=["a"]))

        vm.refresh_from_monitor_result(None)

        assert vm.alerts == ["a"]
