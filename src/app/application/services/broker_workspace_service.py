"""Broker workspace application service."""

from dataclasses import asdict

from app.brokers.bootstrap import BrokerProvider
from app.brokers.shared.enums import ConnectionState
from app.brokers.shared.exceptions import (BrokerAuthenticationException,
                                           BrokerConnectionException)
from app.logging.logging_manager import get_logger
from app.services.broker.connection_status_service import (
    BrokerConnectionSnapshot, ConnectionStatusService)

logger = get_logger(__name__)


class BrokerWorkspaceService:
    """Application-layer broker authentication and connection API."""

    def __init__(
        self,
        broker_provider: BrokerProvider,
        status_service: ConnectionStatusService,
    ) -> None:
        """Initialize broker workspace service."""
        self._provider = broker_provider
        self._status = status_service

    def get_login_url(self) -> str:
        """Return official Breeze login URL."""
        return self._provider.login_url()

    def login(self, session_token: str | None = None) -> BrokerConnectionSnapshot:
        """Login to configured broker."""
        if session_token:
            self._provider.config_provider.store_session_token(session_token)
        self._status.update_state(ConnectionState.CONNECTING)
        try:
            self._provider.manager.connect()
            return self._status.snapshot()
        except BrokerAuthenticationException as error:
            self._status.update_state(ConnectionState.AUTHENTICATION_FAILED)
            logger.warning("Broker login failed: {error}", error=error)
            raise

    def reconnect(self) -> BrokerConnectionSnapshot:
        """Reconnect to broker."""
        self._status.update_state(ConnectionState.RECONNECTING)
        try:
            self._provider.manager.reconnect()
            return self._status.snapshot()
        except (BrokerConnectionException, BrokerAuthenticationException) as error:
            self._status.update_state(ConnectionState.RECONNECT_REQUIRED)
            logger.warning("Broker reconnect failed: {error}", error=error)
            raise

    def logout(self) -> BrokerConnectionSnapshot:
        """Logout and disconnect broker."""
        logger.info("Broker logout requested")
        try:
            self._provider.broker.logout()
        except Exception as error:
            logger.warning("Broker logout error: {error}", error=error)
        self._provider.manager.disconnect()
        return self._status.update_state(ConnectionState.DISCONNECTED, session_valid=False)

    def restore_session(self) -> BrokerConnectionSnapshot:
        """Restore session after application restart."""
        self._status.update_state(ConnectionState.CONNECTING)
        try:
            broker = self._provider.broker
            if broker.auth_service.restore_session():
                broker.connect()
                self._status.update_state(ConnectionState.CONNECTED, session_valid=True)
            else:
                self._status.update_state(ConnectionState.DISCONNECTED)
        except Exception:
            self._status.update_state(ConnectionState.DISCONNECTED)
        return self._status.snapshot()

    def validate_session(self) -> bool:
        """Validate active broker session."""
        broker = self._provider.broker
        valid = broker.auth_service.health_check()
        if not valid:
            self._status.update_state(ConnectionState.SESSION_EXPIRED, session_valid=False)
        return valid

    def get_status(self) -> BrokerConnectionSnapshot:
        """Return current broker connection snapshot."""
        health = self._provider.manager.health()
        self._status.update_state(
            health.connection_state,
            session_valid=health.is_session_valid,
        )
        return self._status.snapshot()

    def get_status_dict(self) -> dict[str, object]:
        """Return status as dictionary for UI binding."""
        return asdict(self.get_status())

    def save_credentials(
        self,
        api_key: str,
        api_secret: str,
        session_token: str = "",
    ) -> None:
        """Store broker credentials securely."""
        provider = self._provider.config_provider
        provider.store_api_key(api_key)
        provider.store_api_secret(api_secret)
        if session_token:
            provider.store_session_token(session_token)
        logger.info(
            "Broker credentials stored for account {account}",
            account=provider.account_name,
        )

    def stop(self) -> None:
        """Stop broker provider."""
        self._provider.stop()
