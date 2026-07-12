"""Broker factory."""

from collections.abc import Callable

from app.brokers.breeze.broker_adapter import BreezeBrokerAdapter
from app.brokers.breeze.session_store import BreezeSessionStore
from app.brokers.broker_interface.interface import BrokerInterface
from app.brokers.dhan.broker import DhanBroker
from app.brokers.shared.enums import BrokerCode
from app.brokers.shared.exceptions import BrokerNotSupportedException
from app.brokers.zerodha.broker import ZerodhaBroker
from app.config.models.app_config import BrokerConfig
from app.events.event_bus import EventBus
from app.security.credential_manager import CredentialManager


class BrokerFactory:
    """Create broker implementations from configuration."""

    def __init__(
        self,
        config: BrokerConfig,
        credential_manager: CredentialManager,
        event_bus: EventBus | None = None,
        *,
        health_callback: object | None = None,
        client_factory: Callable[[str], object] | None = None,
        session_store: BreezeSessionStore | None = None,
    ) -> None:
        """Initialize factory dependencies."""
        self._config = config
        self._credential_manager = credential_manager
        self._event_bus = event_bus
        self._client_factory = client_factory
        self._session_store = session_store

    def create(self, broker_code: str | None = None) -> BrokerInterface:
        """Create a broker instance for the configured code."""
        code = BrokerCode((broker_code or self._config.broker_code).upper())
        if code == BrokerCode.BREEZE:
            return BreezeBrokerAdapter(
                self._config,
                self._credential_manager,
                self._event_bus,
                client_factory=self._client_factory,
                session_store=self._session_store,
            )
        if code == BrokerCode.ZERODHA:
            return ZerodhaBroker(self._config)
        if code == BrokerCode.DHAN:
            return DhanBroker(self._config)
        raise BrokerNotSupportedException(f"Broker not implemented: {code.value}")
