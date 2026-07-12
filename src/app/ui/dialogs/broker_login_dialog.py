"""Broker login dialog."""

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout, QLabel,
                                 QLineEdit, QPushButton, QVBoxLayout, QWidget)

from app.ui.viewmodels.broker_viewmodel import BrokerViewModel


class BrokerLoginDialog(QDialog):
    """Dialog for Breeze OAuth session token entry."""

    def __init__(self, view_model: BrokerViewModel, parent: QWidget | None = None) -> None:
        """Initialize login dialog."""
        super().__init__(parent)
        self._vm = view_model
        self.setWindowTitle("Broker Login — ICICI Breeze")
        self.setMinimumWidth(420)
        self._session_token = QLineEdit()
        self._session_token.setPlaceholderText("Paste session token from Breeze login")
        self._session_token.setEchoMode(QLineEdit.EchoMode.Password)
        self._info = QLabel(
            "Open the official Breeze login page, authenticate, then paste the session token."
        )
        self._info.setWordWrap(True)
        self._open_login = QPushButton("Open Breeze Login Page")
        self._open_login.clicked.connect(self._open_login_page)
        form = QFormLayout()
        form.addRow("Session Token", self._session_token)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self._info)
        layout.addLayout(form)
        layout.addWidget(self._open_login)
        layout.addWidget(buttons)

    def session_token(self) -> str:
        """Return entered session token."""
        return self._session_token.text().strip()

    def _open_login_page(self) -> None:
        url = self._vm.login_url
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _on_accept(self) -> None:
        token = self.session_token()
        if not token:
            self._vm.set_error("Session token is required")
            return
        self._vm.login(token)
        if self._vm.last_error:
            return
        self.accept()
