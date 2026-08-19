"""Strategy list workspace view."""

from PySide6.QtWidgets import QAbstractItemView, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from app.logging.logging_manager import get_logger
from app.ui.strategy.strategy_list_model import StrategyListTableModel
from app.ui.viewmodels.strategy_viewmodel import StrategyViewModel
from app.ui.widgets.common import DataTableWidget, SectionHeader

logger = get_logger(__name__)


class StrategyListView(QWidget):
    """Strategy workspace with list and actions."""

    def __init__(self, viewmodel: StrategyViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = viewmodel
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("Strategies"))
        actions = QHBoxLayout()
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self._open_selected_row)
        actions.addWidget(open_btn)
        for label, cmd in (
            ("Save", viewmodel.save_command),
            ("Refresh", viewmodel.refresh_command),
        ):
            btn = QPushButton(label)
            btn.clicked.connect(cmd.execute)
            actions.addWidget(btn)
        layout.addLayout(actions)
        self._model = StrategyListTableModel(self)
        self._table = DataTableWidget()
        self._table.setModel(self._model)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self._table)
        viewmodel.strategies_changed.connect(self._on_strategies)

    def _on_strategies(self, strategies: list) -> None:
        self._model.set_strategies(strategies)

    def _open_selected_row(self) -> None:
        """Open the selected strategy into Trading, or fall back to the
        viewmodel's "nothing selected" status message when no row is
        selected."""
        rows = self._table.selectionModel().selectedRows()
        strategy_id = self._model.strategy_id_for_row(rows[0].row()) if rows else ""
        logger.debug(
            "Open clicked: selected_row_count={count} strategy_id={strategy_id!r}",
            count=len(rows),
            strategy_id=strategy_id,
        )
        if not strategy_id:
            self._vm.open_command.execute()
            return
        self._vm.open_strategy(strategy_id)
