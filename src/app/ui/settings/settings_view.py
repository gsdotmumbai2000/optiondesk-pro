"""Settings view."""

from dataclasses import replace

from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QLabel,
                               QLineEdit, QPushButton, QVBoxLayout, QWidget)

from app.ui.viewmodels.settings_viewmodel import SettingsViewModel
from app.ui.widgets.common import SectionHeader

_MARKET_MODE_ITEMS = (
    ("Auto (market hours)", "auto"),
    ("Live", "live"),
    ("Simulator", "simulator"),
)


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
        self._market_mode = QComboBox()
        for label, value in _MARKET_MODE_ITEMS:
            self._market_mode.addItem(label, value)
        self._market_status = QLabel()
        form.addRow("Default Exchange", self._exchange)
        form.addRow("Theme", self._theme_btn)
        form.addRow("", self._show_greeks)
        form.addRow("Market Mode", self._market_mode)
        form.addRow("", self._market_status)
        layout.addLayout(form)
        save = QPushButton("Save Preferences")
        save.clicked.connect(self._on_save_clicked)
        layout.addWidget(save)
        prefs = viewmodel.get_preferences()
        self._exchange.setText(prefs.default_exchange)
        self._show_greeks.setChecked(prefs.show_greeks_in_leg_picker)
        self._prefill_market_mode()
        viewmodel.theme_changed.connect(self._theme_btn.setText)
        self._market_mode.currentIndexChanged.connect(self._on_market_mode_changed)
        viewmodel.market_mode_changed.connect(self._on_market_mode_state_changed)

    def _prefill_market_mode(self) -> None:
        index = self._market_mode.findData(self._vm.market_mode)
        if index >= 0:
            self._market_mode.setCurrentIndex(index)
        self._update_market_status_label()

    def _on_market_mode_changed(self, index: int) -> None:
        mode = self._market_mode.itemData(index)
        if mode:
            self._vm.set_market_mode(mode)

    def _on_market_mode_state_changed(self, _payload: dict) -> None:
        self._update_market_status_label()

    def _update_market_status_label(self) -> None:
        active = self._vm.active_broker
        self._market_status.setText(f"Active broker: {active}" if active else "")

    def _on_save_clicked(self) -> None:
        preferences = replace(
            self._vm.get_preferences(),
            default_exchange=self._exchange.text().strip() or "NSE",
            show_greeks_in_leg_picker=self._show_greeks.isChecked(),
        )
        self._vm.save_preferences(preferences)
