"""Broker settings dialog."""

from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout,
                                 QLineEdit, QVBoxLayout, QWidget)

from app.config.models.app_config import BreezeEnvironment
from app.ui.viewmodels.broker_viewmodel import BrokerViewModel


class BrokerSettingsDialog(QDialog):
    """Dialog for broker API credentials and environment."""

    def __init__(self, view_model: BrokerViewModel, parent: QWidget | None = None) -> None:
        """Initialize settings dialog."""
        super().__init__(parent)
        self._vm = view_model
        self.setWindowTitle("Broker Settings — ICICI Breeze")
        self.setMinimumWidth(440)
        self._api_key = QLineEdit()
        self._api_secret = QLineEdit()
        self._api_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self._user_id = QLineEdit()
        self._environment = QComboBox()
        self._environment.addItem("Production", BreezeEnvironment.PRODUCTION.value)
        self._environment.addItem("Sandbox", BreezeEnvironment.SANDBOX.value)
        self._load_fields()
        form = QFormLayout()
        form.addRow("API Key", self._api_key)
        form.addRow("API Secret", self._api_secret)
        form.addRow("User ID", self._user_id)
        form.addRow("Environment", self._environment)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _load_fields(self) -> None:
        self._user_id.setText(self._vm.user_id)
        index = self._environment.findData(self._vm.environment)
        if index >= 0:
            self._environment.setCurrentIndex(index)

    def _on_save(self) -> None:
        api_key = self._api_key.text().strip()
        api_secret = self._api_secret.text().strip()
        if not api_key or not api_secret:
            self._vm.set_error("API key and secret are required")
            return
        self._vm.save_credentials(
            api_key=api_key,
            api_secret=api_secret,
            user_id=self._user_id.text().strip(),
            environment=self._environment.currentData(),
        )
        if self._vm.last_error:
            return
        self.accept()
