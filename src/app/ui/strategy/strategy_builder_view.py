"""Strategy builder view."""

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.charts import greeks_chart, payoff_chart
from app.ui.viewmodels.trading_viewmodel import TradingViewModel
from app.ui.widgets.common import DataTableWidget, SectionHeader


class StrategyBuilderView(QWidget):
    """Strategy leg grid, summary, and action buttons."""

    def __init__(self, viewmodel: TradingViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = viewmodel
        root = QVBoxLayout(self)
        root.addWidget(SectionHeader("Strategy Builder"))
        btn_row = QHBoxLayout()
        for label, cmd in (
            ("Evaluate", viewmodel.evaluate_command),
            ("Refresh Margin", viewmodel.refresh_margin_command),
            ("Optimize", viewmodel.optimize_command),
            ("Save", viewmodel.save_command),
            ("Load", viewmodel.load_command),
        ):
            b = QPushButton(label)
            b.clicked.connect(cmd.execute)
            btn_row.addWidget(b)
        root.addLayout(btn_row)
        self._leg_table = DataTableWidget()
        root.addWidget(self._leg_table)
        self._summary = QLabel("Strategy summary placeholder")
        root.addWidget(self._summary)
        self._margin_summary = QLabel(viewmodel.margin_summary)
        root.addWidget(self._margin_summary)
        charts = QGridLayout()
        # Real chart widgets, ready for evaluate_command's PayoffResult/
        # GreeksResult via self._payoff_chart.set_curve()/
        # self._greeks_chart.set_greeks() once that command builds a real
        # StrategyEvaluationRequest instead of its current placeholder.
        self._payoff_chart = payoff_chart()
        self._greeks_chart = greeks_chart()
        charts.addWidget(self._payoff_chart, 0, 0)
        charts.addWidget(self._greeks_chart, 0, 1)
        root.addLayout(charts)
        prob = QLabel("Probability summary — from engine results")
        root.addWidget(prob)
        viewmodel.summary_changed.connect(self._summary.setText)
        viewmodel.margin_summary_changed.connect(self._margin_summary.setText)
