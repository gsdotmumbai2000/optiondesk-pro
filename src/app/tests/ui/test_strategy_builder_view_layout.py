"""Regression test: the Strategy Builder's leg table must actually grow as
the window grows, not sit at a fixed height while sibling widgets (charts,
summary labels) soak up the extra space -- previously every widget in the
builder's QVBoxLayout had the same (default, unset) stretch factor, so the
table stayed squeezed to a small sliver regardless of available room. It
must also be independently, manually resizable (drag the splitter handle
against the charts pane), not just auto-stretch proportionally.
"""

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter

from app.ui.strategy.strategy_builder_view import StrategyBuilderView


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


class _FakeCommand:
    def execute(self) -> None:
        pass


class _FakeTradingViewModel(QObject):
    strategy_name_changed = Signal(str)
    summary_changed = Signal(str)
    margin_summary_changed = Signal(str)
    evaluation_changed = Signal(object)
    optimization_changed = Signal(object)
    paper_trade_changed = Signal(object)
    pending_legs_changed = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.evaluate_command = _FakeCommand()
        self.refresh_margin_command = _FakeCommand()
        self.optimize_command = _FakeCommand()
        self.paper_trade_command = _FakeCommand()
        self.margin_summary = "Margin: —"


class TestLegTableStretchesWithWindow:
    def test_leg_table_grows_when_window_grows(self, qapp: QApplication) -> None:
        view = StrategyBuilderView(_FakeTradingViewModel())
        window = QMainWindow()
        window.setCentralWidget(view)

        window.resize(900, 500)
        window.show()
        qapp.processEvents()
        short_height = view._leg_table.height()

        window.resize(900, 1000)
        qapp.processEvents()
        tall_height = view._leg_table.height()

        window.close()
        assert tall_height > short_height * 1.5  # substantial growth, not a rounding blip


class TestLegTableIsManuallyDraggable:
    def test_dragging_the_splitter_handle_resizes_the_leg_table_pane(self, qapp: QApplication) -> None:
        view = StrategyBuilderView(_FakeTradingViewModel())
        window = QMainWindow()
        window.setCentralWidget(view)
        window.resize(900, 900)
        window.show()
        qapp.processEvents()
        splitter = view.findChildren(QSplitter)[0]
        assert splitter.count() == 2
        starting_height = view._leg_table.height()

        sizes = splitter.sizes()
        splitter.setSizes([sizes[0] + 250, max(sizes[1] - 250, 20)])
        qapp.processEvents()

        window.close()
        assert view._leg_table.height() > starting_height + 100
