"""Strategy list workspace view."""

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from app.ui.viewmodels.strategy_viewmodel import StrategyViewModel
from app.ui.widgets.common import DataTableWidget, SectionHeader


class StrategyListView(QWidget):
    """Strategy workspace with list and actions."""

    def __init__(self, viewmodel: StrategyViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = viewmodel
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("Strategies"))
        actions = QHBoxLayout()
        for label, cmd in (
            ("Open", viewmodel.open_command),
            ("Save", viewmodel.save_command),
            ("Refresh", viewmodel.refresh_command),
        ):
            btn = QPushButton(label)
            btn.clicked.connect(cmd.execute)
            actions.addWidget(btn)
        layout.addLayout(actions)
        self._table = DataTableWidget()
        layout.addWidget(self._table)
        viewmodel.strategies_changed.connect(self._on_strategies)

    def _on_strategies(self, strategies: list) -> None:
        self._table.setToolTip(f"{len(strategies)} strategies loaded")
