"""Broker connection ViewModel."""

from PySide6.QtCore import Property, Signal

from app.brokers.shared.enums import BrokerConnectionStatus
from app.brokers.shared.exceptions import BrokerAuthenticationException
from app.ui.commands.ui_command import RelayCommand
from app.ui.viewmodels.base_viewmodel import BaseViewModel
from app.ui.viewmodels.context import ViewModelContext


class BrokerViewModel(BaseViewModel):
    """ViewModel for broker authentication and connection status."""

    status_changed = Signal(dict)
    login_url_changed = Signal(str)

    def __init__(self, ctx: ViewModelContext, parent=None) -> None:
        """Initialize broker view model."""
        super().__init__(parent)
        self._ctx = ctx
        self._broker_name = "ICICI Breeze"
        self._status = BrokerConnectionStatus.DISCONNECTED
        self._user_id = ""
        self._environment = "production"
        self._login_url = ""
        self._last_error = ""
        self.login_command = RelayCommand(self.login_from_stored, parent=self)
        self.logout_command = RelayCommand(self.logout, parent=self)
        self.reconnect_command = RelayCommand(self.reconnect, parent=self)
        self.refresh_status_command = RelayCommand(self.refresh_status, parent=self)
        self._wire_events()
        self.refresh_status()

    @Property(str, notify=status_changed)
    def broker_name(self) -> str:
        return self._broker_name

    @Property(str, notify=status_changed)
    def connection_status(self) -> str:
        return self._status.value

    @Property(str, notify=status_changed)
    def user_id(self) -> str:
        return self._user_id

    @Property(str, notify=status_changed)
    def environment(self) -> str:
        return self._environment

    @Property(str, notify=login_url_changed)
    def login_url(self) -> str:
        return self._login_url

    @property
    def last_error(self) -> str:
        return self._last_error

    def set_error(self, message: str) -> None:
        """Set and emit last error."""
        self._last_error = message
        self.error_occurred.emit(message)

    def login(self, session_token: str) -> None:
        """Login with session token."""
        self._last_error = ""
        service = self._broker_service()
        if service is None:
            self._last_error = "Broker service unavailable"
            return
        self.busy = True
        try:
            snap = service.login(session_token)
            self._apply_snapshot(snap)
            self.status_message = "Broker connected"
        except BrokerAuthenticationException as error:
            self._last_error = str(error)
            self.set_error(str(error))
        finally:
            self.busy = False

    def login_from_stored(self) -> None:
        """Login using stored credentials."""
        self.login("")

    def logout(self) -> None:
        """Logout broker."""
        service = self._broker_service()
        if service is None:
            return
        snap = service.logout()
        self._apply_snapshot(snap)
        self.status_message = "Broker disconnected"

    def reconnect(self) -> None:
        """Reconnect broker."""
        service = self._broker_service()
        if service is None:
            return
        self.busy = True
        try:
            snap = service.reconnect()
            self._apply_snapshot(snap)
            self.status_message = "Broker reconnected"
        except Exception as error:
            self.set_error(str(error))
        finally:
            self.busy = False

    def refresh_status(self) -> None:
        """Refresh connection status from service."""
        service = self._broker_service()
        if service is None:
            return
        snap = service.get_status()
        self._apply_snapshot(snap)
        self._login_url = service.get_login_url()
        self.login_url_changed.emit(self._login_url)

    def save_credentials(
        self,
        api_key: str,
        api_secret: str,
        user_id: str = "",
        environment: str = "production",
    ) -> None:
        """Save broker credentials."""
        self._last_error = ""
        service = self._broker_service()
        if service is None:
            self._last_error = "Broker service unavailable"
            return
        service.save_credentials(api_key, api_secret)
        self._user_id = user_id
        self._environment = environment
        self.status_message = "Broker credentials saved"

    def _apply_snapshot(self, snap: object) -> None:
        self._broker_name = getattr(snap, "broker_name", self._broker_name)
        status = getattr(snap, "status", self._status)
        self._status = status
        self._user_id = getattr(snap, "user_id", self._user_id)
        self._environment = getattr(snap, "environment", self._environment)
        payload = {
            "broker_name": self._broker_name,
            "status": self._status,
            "user_id": self._user_id,
            "environment": self._environment,
        }
        self.status_changed.emit(payload)

    def _broker_service(self):
        return self._ctx.provider.broker

    def _wire_events(self) -> None:
        events = self._ctx.events
        events.broker_connected.connect(lambda _: self.refresh_status())
        events.broker_disconnected.connect(lambda _: self.refresh_status())
        events.session_expired.connect(lambda _: self.refresh_status())
        events.authentication_succeeded.connect(lambda _: self.refresh_status())
        events.authentication_failed.connect(lambda _: self.refresh_status())
