"""Settings view."""

from dataclasses import replace

from PySide6.QtWidgets import QCheckBox, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget

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
        self._show_greeks = QCheckBox("Show Greeks (Delta) in the Add Leg strike picker")
        form.addRow("Default Exchange", self._exchange)
        form.addRow("Theme", self._theme_btn)
        form.addRow("", self._show_greeks)
        layout.addLayout(form)
        save = QPushButton("Save Preferences")
        save.clicked.connect(self._on_save_clicked)
        layout.addWidget(save)
        prefs = viewmodel.get_preferences()
        self._exchange.setText(prefs.default_exchange)
        self._show_greeks.setChecked(prefs.show_greeks_in_leg_picker)
        viewmodel.theme_changed.connect(self._theme_btn.setText)

    def _on_save_clicked(self) -> None:
        preferences = replace(
            self._vm.get_preferences(),
            default_exchange=self._exchange.text().strip() or "NSE",
            show_greeks_in_leg_picker=self._show_greeks.isChecked(),
        )
        self._vm.save_preferences(preferences)
