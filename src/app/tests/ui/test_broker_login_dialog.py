"""Regression tests for BrokerLoginDialog's stored-session-first behavior.

The dialog previously required pasting a fresh session token on every open,
even though the app already reuses the stored token automatically at
startup. Restarting during development (a code change, not a real Breeze
session expiry) shouldn't force a manual browser round-trip when the stored
token would still work -- the dialog should try it first and only fall back
to manual entry when Breeze itself actually rejects it.
"""

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication, QDialog

from app.ui.dialogs.broker_login_dialog import BrokerLoginDialog


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


class _FakeBrokerViewModel:
    """Minimal BrokerViewModel double."""

    def __init__(self, *, stored_session_error: str = "") -> None:
        self.login_url = "https://api.icicidirect.com/apiuser/login?api_key=x"
        self.last_error = ""
        self._stored_session_error = stored_session_error
        self.login_from_stored_calls = 0
        self.login_calls: list[str] = []

    def login_from_stored(self) -> None:
        self.login_from_stored_calls += 1
        self.last_error = self._stored_session_error
        # Once the stored attempt has been exercised, simulate a fresh
        # manual paste succeeding (mirrors login() clearing last_error).
        self._stored_session_error = ""

    def login(self, token: str) -> None:
        self.login_calls.append(token)
        self.last_error = ""

    def set_error(self, message: str) -> None:
        self.last_error = message


class _RaisingBrokerViewModel:
    """Reproduces the live incident: BrokerManager.connect() re-wraps
    BrokerAuthenticationException as BrokerConnectionException, which
    BrokerViewModel.login()'s narrower except clause does not catch, so the
    exception escapes login()/login_from_stored() instead of being captured
    into last_error."""

    def __init__(self) -> None:
        self.login_url = "https://api.icicidirect.com/apiuser/login?api_key=x"
        self.last_error = ""

    def login_from_stored(self) -> None:
        raise RuntimeError("Unexpected error: Could not authenticate credentials.")

    def login(self, token: str) -> None:
        raise RuntimeError("Unexpected error: Could not authenticate credentials.")

    def set_error(self, message: str) -> None:
        self.last_error = message


def _pump() -> None:
    """Let the dialog's QTimer.singleShot(0, ...) fire."""
    for _ in range(10):
        QCoreApplication.processEvents()


class TestStoredSessionTriedFirst:
    def test_valid_stored_session_auto_accepts_without_typing_anything(
        self, qapp: QApplication
    ) -> None:
        vm = _FakeBrokerViewModel(stored_session_error="")
        dialog = BrokerLoginDialog(vm)
        dialog.show()

        _pump()

        assert vm.login_from_stored_calls == 1
        assert vm.login_calls == []  # never had to type/submit a new token
        assert dialog.result() == QDialog.DialogCode.Accepted

    def test_expired_stored_session_leaves_dialog_open_for_manual_entry(
        self, qapp: QApplication
    ) -> None:
        vm = _FakeBrokerViewModel(stored_session_error="Could not authenticate credentials.")
        dialog = BrokerLoginDialog(vm)
        dialog.show()

        _pump()

        assert vm.login_from_stored_calls == 1
        assert dialog.result() != QDialog.DialogCode.Accepted
        assert dialog.isVisible()
        assert "Could not authenticate credentials." in dialog._status_label.text()  # noqa: SLF001
        assert dialog._session_token.isEnabled()  # noqa: SLF001

    def test_manual_entry_still_works_after_stored_session_fails(
        self, qapp: QApplication
    ) -> None:
        vm = _FakeBrokerViewModel(stored_session_error="expired")
        dialog = BrokerLoginDialog(vm)
        dialog.show()
        _pump()
        assert not dialog.isHidden() or dialog.result() != QDialog.DialogCode.Accepted

        dialog._session_token.setText("fresh-token-123")  # noqa: SLF001
        dialog._on_accept()  # noqa: SLF001

        assert vm.login_calls == ["fresh-token-123"]
        assert dialog.result() == QDialog.DialogCode.Accepted


class TestUncaughtExceptionDoesNotStickDialogInBusyState:
    """Live incident: an exception escaping login_from_stored()/login()
    (not just a populated last_error) must still leave the dialog usable."""

    def test_exception_from_stored_attempt_is_shown_and_unblocks_manual_entry(
        self, qapp: QApplication
    ) -> None:
        vm = _RaisingBrokerViewModel()
        dialog = BrokerLoginDialog(vm)
        dialog.show()

        _pump()

        assert dialog.result() != QDialog.DialogCode.Accepted
        assert "Could not authenticate credentials." in dialog._status_label.text()  # noqa: SLF001
        # Must not be stuck busy: fields/buttons re-enabled for manual entry.
        assert dialog._session_token.isEnabled()  # noqa: SLF001
        assert dialog._try_stored.isEnabled()  # noqa: SLF001
        assert dialog._open_login.isEnabled()  # noqa: SLF001

    def test_exception_from_manual_submit_is_shown_not_raised(
        self, qapp: QApplication
    ) -> None:
        class _StoredOkButManualLoginRaises(_FakeBrokerViewModel):
            def login(self, token: str) -> None:
                raise RuntimeError("Unexpected error: Could not authenticate credentials.")

        vm = _StoredOkButManualLoginRaises(stored_session_error="expired")
        dialog = BrokerLoginDialog(vm)
        dialog.show()
        _pump()
        assert dialog.result() != QDialog.DialogCode.Accepted  # stored attempt failed normally

        dialog._session_token.setText("fresh-token-123")  # noqa: SLF001
        dialog._on_accept()  # noqa: SLF001 - must not raise

        assert dialog.result() != QDialog.DialogCode.Accepted
        assert "Could not authenticate credentials." in dialog._status_label.text()  # noqa: SLF001
