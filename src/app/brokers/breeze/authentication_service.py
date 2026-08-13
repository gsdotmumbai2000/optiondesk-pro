"""Breeze authentication service with events and retry."""

from app.brokers.breeze.authentication import BreezeAuthentication
from app.brokers.breeze.configuration_provider import BreezeConfigurationProvider
from app.brokers.breeze.constants import login_url
from app.brokers.breeze.session_store import BreezeSessionStore
from app.brokers.events import (AuthenticationFailedEvent,
                                AuthenticationSucceededEvent)
from app.brokers.shared.exceptions import (BrokerAuthenticationException,
                                           BrokerConnectionException,
                                           BrokerTimeoutException)
from app.brokers.shared.retry import retry_call
from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger

logger = get_logger(__name__)


class BreezeAuthenticationService:
    """Production Breeze login, logout, reconnect, and validation."""

    def __init__(
        self,
        auth: BreezeAuthentication,
        config_provider: BreezeConfigurationProvider,
        session_store: BreezeSessionStore | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize authentication service."""
        self._auth = auth
        self._config = config_provider
        self._session_store = session_store
        self._event_bus = event_bus

    @property
    def session_token(self) -> str:
        """Return active session token."""
        return self._auth.session_token

    def login_url(self) -> str:
        """Return official Breeze OAuth login URL."""
        api_key = self._config.get_api_key() or ""
        return login_url(api_key)

    def login(self, session_token: str | None = None) -> None:
        """Authenticate with optional new session token.

        Does not publish AuthenticationSucceededEvent: the Breeze API call
        succeeding does not yet mean the session is usable for other calls
        (BreezeSessionManager.mark_authenticated() has not run and broker
        state is not CONNECTED). Callers must call publish_authenticated()
        once the session is actually ready.
        """
        logger.info(
            "Breeze login started for account {account}",
            account=self._config.account_name,
        )
        if session_token:
            self._config.store_session_token(session_token)
        self._authenticate_with_retry()
        logger.info("Breeze authentication API succeeded")

    def reconnect(self) -> None:
        """Reconnect using stored credentials.

        See login() docstring: publish_authenticated() is the caller's
        responsibility once the session is actually ready.
        """
        logger.info(
            "Breeze reconnect for account {account}",
            account=self._config.account_name,
        )
        self._authenticate_with_retry()
        logger.info("Breeze authentication API succeeded")

    def restore_session(self) -> bool:
        """Restore session after application restart."""
        snapshot = self._session_store.load() if self._session_store else None
        if snapshot is None or not snapshot.is_valid:
            return False
        if not self._config.has_credentials():
            return False
        try:
            self._auth.authenticate()
            return self.validate_session()
        except BrokerAuthenticationException:
            return False

    def logout(self) -> None:
        """Clear session and persisted metadata."""
        logger.info(
            "Breeze logout for account {account}",
            account=self._config.account_name,
        )
        self._auth.logout()
        if self._session_store is not None:
            self._session_store.clear()

    def validate_session(self) -> bool:
        """Validate active session with Breeze API."""
        return self._auth.validate_session()

    def health_check(self) -> bool:
        """Run connection health check."""
        if not self._auth.session_token:
            return False
        return self.validate_session()

    def refresh_session(self) -> None:
        """Refresh session using stored token."""
        logger.info("Breeze session refresh requested")
        self._authenticate_with_retry()

    def persist_session(self) -> None:
        """Persist session metadata after successful auth."""
        if self._session_store is None:
            return
        snapshot = BreezeSessionStore.build_snapshot(
            self._config.account_name,
            self._config.user_id,
            self._config.environment,
        )
        self._session_store.save(snapshot)

    def _authenticate_with_retry(self) -> None:
        """Authenticate with exponential backoff."""
        try:
            retry_call(
                self._auth.authenticate,
                max_retries=self._config.config.reconnect_max_retries,
                backoff_ms=self._config.config.reconnect_backoff_ms,
                retry_on=(
                    BrokerConnectionException,
                    BrokerTimeoutException,
                    BrokerAuthenticationException,
                ),
            )
        except BrokerAuthenticationException as error:
            self._publish_failure(str(error))
            raise

    def publish_authenticated(self) -> None:
        """Publish AuthenticationSucceededEvent.

        Call only once the broker session is fully ready for normal API
        calls (session marked authenticated, state CONNECTED) — this event
        is interpreted by the rest of the app as "broker session usable".
        """
        self.persist_session()
        payload = {
            "broker": self._config.broker_code,
            "account": self._config.account_name,
            "user_id": self._config.user_id,
            "environment": self._config.environment.value,
        }
        logger.info("AuthenticationSucceededEvent published")
        self._publish(AuthenticationSucceededEvent(payload=payload))

    def _publish_failure(self, reason: str) -> None:
        """Publish authentication failure event."""
        payload = {
            "broker": self._config.broker_code,
            "account": self._config.account_name,
            "reason": reason,
        }
        logger.warning("Breeze authentication failed: {reason}", reason=reason)
        self._publish(AuthenticationFailedEvent(payload=payload))

    def _publish(self, event: object) -> None:
        """Publish event to bus."""
        if self._event_bus is not None:
            self._event_bus.publish(event)
