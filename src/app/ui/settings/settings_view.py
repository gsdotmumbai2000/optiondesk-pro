"""Settings view."""

from PySide6.QtWidgets import QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget

from app.ui.viewmodels.settings_viewmodel import SettingsViewModel
from app.ui.widgets.common import SectionHeader


class SettingsView(QWidget):
    """Theme and user preferences."""

    def __init__(self, viewmodel: SettingsViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = viewmodel
        layout = QVBoxLayout(self)
        layout.addWidget(SectionHeader("Settings"))
        form = QFormLayout()
        self._exchange = QLineEdit()
        self._theme_btn = QPushButton("Cycle Theme")
        self._theme_btn.clicked.connect(viewmodel.apply_theme_command.execute)
        form.addRow("Default Exchange", self._exchange)
        form.addRow("Theme", self._theme_btn)
        layout.addLayout(form)
        save = QPushButton("Save Preferences")
        save.clicked.connect(viewmodel.save_command.execute)
        layout.addWidget(save)
        prefs = viewmodel.get_preferences()
        self._exchange.setText(prefs.default_exchange)
        viewmodel.theme_changed.connect(self._theme_btn.setText)
