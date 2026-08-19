"""Strategy builder view."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                                 QPushButton, QSplitter, QVBoxLayout, QWidget)

from app.ui.charts import greeks_chart, payoff_chart
from app.ui.dialogs.add_leg_dialog import AddLegDialog
from app.ui.dialogs.open_dialog import OpenDialog
from app.ui.strategy.leg_table_model import StrategyLegTableModel
from app.ui.viewmodels.trading_viewmodel import TradingViewModel
from app.ui.widgets.common import DataTableWidget, SectionHeader, style_splitter_handle


class StrategyBuilderView(QWidget):
    """Strategy leg grid, summary, and action buttons."""

    def __init__(self, viewmodel: TradingViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = viewmodel
        root = QVBoxLayout(self)
        root.addWidget(SectionHeader("Strategy Builder"))
        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._on_save_clicked)
        for label, cmd in (
            ("Evaluate", viewmodel.evaluate_command),
            ("Refresh Margin", viewmodel.refresh_margin_command),
            ("Optimize", viewmodel.optimize_command),
            ("Paper Trade", viewmodel.paper_trade_command),
        ):
            b = QPushButton(label)
            b.clicked.connect(cmd.execute)
            btn_row.addWidget(b)
        btn_row.addWidget(save_btn)
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self._on_load_clicked)
        btn_row.addWidget(load_btn)
        root.addLayout(btn_row)

        build_row = QHBoxLayout()
        self._name_field = QLineEdit()
        self._name_field.setPlaceholderText("Strategy name")
        build_row.addWidget(self._name_field)
        new_btn = QPushButton("New Strategy")
        new_btn.clicked.connect(self._on_new_strategy)
        build_row.addWidget(new_btn)
        add_leg_btn = QPushButton("Add Leg")
        add_leg_btn.clicked.connect(self._on_add_leg)
        build_row.addWidget(add_leg_btn)
        remove_leg_btn = QPushButton("Remove Leg")
        remove_leg_btn.clicked.connect(self._on_remove_leg)
        build_row.addWidget(remove_leg_btn)
        root.addLayout(build_row)

        self._leg_model = StrategyLegTableModel(self)
        self._leg_table = DataTableWidget()
        self._leg_table.setModel(self._leg_model)

        # A QSplitter, not a plain stacked QVBoxLayout: the leg table and
        # the charts both want real, user-controllable room, not just
        # whatever proportion a fixed stack happens to give them. Drag the
        # handle between the two panes to reallocate space either way.
        legs_pane = QWidget()
        legs_layout = QVBoxLayout(legs_pane)
        legs_layout.setContentsMargins(0, 0, 0, 0)
        legs_layout.addWidget(self._leg_table)
        self._summary = QLabel("Strategy summary placeholder")
        legs_layout.addWidget(self._summary)
        self._margin_summary = QLabel(viewmodel.margin_summary)
        legs_layout.addWidget(self._margin_summary)

        results_pane = QWidget()
        results_layout = QVBoxLayout(results_pane)
        results_layout.setContentsMargins(0, 0, 0, 0)
        charts = QGridLayout()
        self._payoff_chart = payoff_chart()
        self._greeks_chart = greeks_chart()
        charts.addWidget(self._payoff_chart, 0, 0)
        charts.addWidget(self._greeks_chart, 0, 1)
        results_layout.addLayout(charts)
        prob = QLabel("Probability summary — from engine results")
        results_layout.addWidget(prob)
        self._optimization_summary = QLabel("Optimization: not run yet")
        results_layout.addWidget(self._optimization_summary)
        self._paper_trade_summary = QLabel("Paper account: not traded yet")
        results_layout.addWidget(self._paper_trade_summary)

        builder_splitter = QSplitter(Qt.Orientation.Vertical)
        builder_splitter.addWidget(legs_pane)
        builder_splitter.addWidget(results_pane)
        builder_splitter.setStretchFactor(0, 1)
        builder_splitter.setStretchFactor(1, 1)
        style_splitter_handle(builder_splitter)
        root.addWidget(builder_splitter, 1)

        viewmodel.summary_changed.connect(self._summary.setText)
        viewmodel.margin_summary_changed.connect(self._margin_summary.setText)
        viewmodel.evaluation_changed.connect(self._on_evaluation)
        viewmodel.optimization_changed.connect(self._on_optimization)
        viewmodel.paper_trade_changed.connect(self._on_paper_trade)
        viewmodel.pending_legs_changed.connect(self._leg_model.set_legs)
        viewmodel.strategy_name_changed.connect(self._name_field.setText)

    def _on_load_clicked(self) -> None:
        """Show a picker of saved strategies and load the selected one's
        legs into the builder via TradingViewModel.load_strategy()."""
        dialog = OpenDialog(self._vm.list_strategies(), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._vm.load_strategy(dialog.selected_id())

    def _on_evaluation(self, snapshot) -> None:
        """Render the latest evaluate_command result (a LiveAnalyticsSnapshot)
        into the payoff/Greeks charts, clearing either that the snapshot
        doesn't carry (e.g. an empty-legs strategy has no payoff)."""
        if snapshot.payoff is not None:
            self._payoff_chart.set_curve(snapshot.payoff.payoff_curve)
        else:
            self._payoff_chart.clear()
        if snapshot.greeks is not None:
            self._greeks_chart.set_greeks(snapshot.greeks)
        else:
            self._greeks_chart.clear()

    def _on_optimization(self, result) -> None:
        """Render the latest optimize_command result (an OptimizationResult)
        as a one-line summary: how many candidates ranked, the best score,
        and the engine's recommendation."""
        self._optimization_summary.setText(
            f"Optimization: {len(result.candidate_strategies)} candidates ranked | "
            f"Best score: {result.overall_score} | {result.recommendation}"
        )

    def _on_paper_trade(self, snapshot) -> None:
        """Render the latest paper_trade_command result (a
        PaperAccountSnapshot) as a one-line account summary."""
        self._paper_trade_summary.setText(
            f"Paper account: equity {snapshot.equity} | cash {snapshot.cash_balance} | "
            f"{len(snapshot.open_positions)} open position(s) | realized P&L {snapshot.realized_pnl}"
        )

    def _on_new_strategy(self) -> None:
        self._name_field.clear()
        self._vm.new_strategy()

    def _on_add_leg(self) -> None:
        AddLegDialog(self._vm, self).exec()

    def _on_remove_leg(self) -> None:
        rows = self._leg_table.selectionModel().selectedRows()
        if not rows:
            return
        leg_id = self._leg_model.leg_id_for_row(rows[0].row())
        if leg_id:
            self._vm.remove_leg(leg_id)

    def _on_save_clicked(self) -> None:
        self._vm.save_new_strategy(self._name_field.text().strip())
