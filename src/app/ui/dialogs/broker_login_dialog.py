"""Broker login dialog."""

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout, QLabel,
                                 QLineEdit, QPushButton, QVBoxLayout, QWidget)

from app.ui.viewmodels.broker_viewmodel import BrokerViewModel


class BrokerLoginDialog(QDialog):
    """Dialog for Breeze OAuth session token entry.

    Always tries the already-stored session token first -- Breeze session
    tokens commonly remain valid across app restarts (including ones caused
    by a code change during development), so a fresh browser round-trip
    should only be necessary once Breeze itself actually rejects the stored
    token, not on every restart as a matter of habit.
    """

    def __init__(self, view_model: BrokerViewModel, parent: QWidget | None = None) -> None:
        """Initialize login dialog."""
        super().__init__(parent)
        self._vm = view_model
        self.setWindowTitle("Broker Login — ICICI Breeze")
        self.setMinimumWidth(420)
        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        self._try_stored = QPushButton("Try Stored Session")
        self._try_stored.clicked.connect(self._try_stored_session)
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
        layout.addWidget(self._status_label)
        layout.addWidget(self._try_stored)
        layout.addWidget(self._info)
        layout.addLayout(form)
        layout.addWidget(self._open_login)
        layout.addWidget(buttons)
        # Deferred so the dialog paints first instead of appearing to hang
        # while the (synchronous, blocking) stored-session attempt runs.
        QTimer.singleShot(0, self._try_stored_session)

    def session_token(self) -> str:
        """Return entered session token."""
        return self._session_token.text().strip()

    def _open_login_page(self) -> None:
        url = self._vm.login_url
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _try_stored_session(self) -> None:
        """Attempt to reuse the already-stored session token before asking
        the user to paste a new one -- only a real rejection from Breeze
        should require that.

        Broker/network failures are not guaranteed to surface as the
        BrokerAuthenticationException the ViewModel's own try/except
        expects (BrokerManager.connect() can re-wrap any failure, auth or
        not, as BrokerConnectionException), so this catches broadly rather
        than trusting `last_error` alone -- otherwise an unexpected
        exception type escapes uncaught and leaves the dialog stuck in its
        busy state with no way to fall back to manual entry.
        """
        self._set_busy(True)
        self._status_label.setText("Checking stored session…")
        try:
            self._vm.login_from_stored()
        except Exception as error:  # noqa: BLE001 - must never leave the dialog stuck
            self._vm.set_error(str(error))
        if self._vm.last_error:
            self._status_label.setText(
                f"Stored session no longer valid: {self._vm.last_error}\n"
                "Paste a new session token below."
            )
            self._set_busy(False)
            return
        self._status_label.setText("Connected using stored session.")
        self.accept()

    def _set_busy(self, busy: bool) -> None:
        self._try_stored.setEnabled(not busy)
        self._session_token.setEnabled(not busy)
        self._open_login.setEnabled(not busy)

    def _on_accept(self) -> None:
        token = self.session_token()
        if not token:
            self._vm.set_error("Session token is required")
            return
        try:
            self._vm.login(token)
        except Exception as error:  # noqa: BLE001 - see _try_stored_session
            self._vm.set_error(str(error))
        if self._vm.last_error:
            self._status_label.setText(f"Login failed: {self._vm.last_error}")
            return
        self.accept()
