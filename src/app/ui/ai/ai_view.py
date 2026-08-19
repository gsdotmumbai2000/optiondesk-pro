"""AI recommendation view."""

from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTextEdit, QVBoxLayout, QWidget

from app.ui.viewmodels.ai_viewmodel import AIViewModel
from app.ui.widgets.common import DataTableWidget, SectionHeader

_HEADERS = ("Category", "Priority", "Confidence", "Summary", "Suggested Action")


class AIView(QWidget):
    """Recommendations, explanation, alternatives, confidence."""

    def __init__(self, viewmodel: AIViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = viewmodel
        layout = QVBoxLayout(self)
        btns = QHBoxLayout()
        gen = QPushButton("Generate Recommendation")
        gen.clicked.connect(viewmodel.generate_command.execute)
        hist = QPushButton("History")
        hist.clicked.connect(viewmodel.history_command.execute)
        btns.addWidget(gen)
        btns.addWidget(hist)
        layout.addLayout(btns)
        layout.addWidget(SectionHeader("Recommendations"))
        self._table = DataTableWidget()
        self._table_model = QStandardItemModel(0, len(_HEADERS), self)
        self._table_model.setHorizontalHeaderLabels(list(_HEADERS))
        self._table.setModel(self._table_model)
        layout.addWidget(self._table)
        layout.addWidget(SectionHeader("Explanation"))
        self._explanation = QTextEdit()
        self._explanation.setReadOnly(True)
        layout.addWidget(self._explanation)
        layout.addWidget(SectionHeader("Alternative Strategies"))
        viewmodel.recommendations_changed.connect(self._on_recommendations)

    def _on_recommendations(self, recommendations: list) -> None:
        """Populate the recommendations table and show the primary
        recommendation's explanation (empty when there are none)."""
        self._table_model.setRowCount(0)
        for rec in recommendations:
            row = [
                QStandardItem(str(rec.category.value)),
                QStandardItem(str(rec.priority.value)),
                QStandardItem(str(rec.confidence_score)),
                QStandardItem(rec.summary),
                QStandardItem(rec.suggested_action),
            ]
            self._table_model.appendRow(row)
        primary = max(recommendations, key=lambda r: r.scores.priority_score, default=None)
        self._explanation.setPlainText(primary.detailed_explanation.why if primary else "")
