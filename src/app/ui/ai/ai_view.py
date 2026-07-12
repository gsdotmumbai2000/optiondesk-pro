"""AI recommendation view."""

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTextEdit, QVBoxLayout, QWidget

from app.ui.viewmodels.ai_viewmodel import AIViewModel
from app.ui.widgets.common import DataTableWidget, SectionHeader


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
        layout.addWidget(self._table)
        layout.addWidget(SectionHeader("Explanation"))
        self._explanation = QTextEdit()
        self._explanation.setReadOnly(True)
        layout.addWidget(self._explanation)
        layout.addWidget(SectionHeader("Alternative Strategies"))
