"""Breeze session manager."""

from datetime import datetime, timedelta, timezone

from app.brokers.breeze.authentication import BreezeAuthentication
from app.brokers.shared.exceptions import BrokerSessionExpiredException
from app.config.models.app_config import BrokerConfig


class BreezeSessionManager:
    """Track and validate Breeze session lifecycle."""

    def __init__(
        self,
        auth: BreezeAuthentication,
        config: BrokerConfig,
    ) -> None:
        """Initialize session manager."""
        self._auth = auth
        self._config = config
        self._session_started: datetime | None = None

    def mark_authenticated(self) -> None:
        """Record successful authentication time."""
        self._session_started = datetime.now(timezone.utc)

    def is_session_valid(self) -> bool:
        """Return whether session is within configured timeout."""
        if self._session_started is None:
            return False
        if not self._auth.validate_session():
            return False
        elapsed = datetime.now(timezone.utc) - self._session_started
        return elapsed < timedelta(minutes=self._config.session_timeout_min)

    def refresh_session(self) -> None:
        """Refresh session or raise expiry error."""
        if not self._auth.session_token:
            raise BrokerSessionExpiredException("No active Breeze session")
        self._auth.refresh_session()
        if not self._auth.validate_session():
            raise BrokerSessionExpiredException("Breeze session refresh failed")
        self.mark_authenticated()

    def logout(self) -> None:
        """Logout and clear session."""
        self._auth.logout()
        self._session_started = None
