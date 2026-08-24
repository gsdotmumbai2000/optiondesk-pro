"""Broker integration bootstrap."""

from pathlib import Path

from app.brokers.broker_factory.factory import BrokerFactory
from app.brokers.broker_manager.manager import BrokerManager
from app.brokers.breeze.configuration_provider import BreezeConfigurationProvider
from app.brokers.breeze.constants import login_url
from app.brokers.breeze.session_store import BreezeSessionStore
from app.config.models.app_config import BrokerConfig
from app.events.event_bus import EventBus
from app.security.credential_manager import CredentialManager


class BrokerProvider:
    """Factory for broker services."""

    def __init__(
        self,
        config: BrokerConfig,
        credential_manager: CredentialManager,
        event_bus: EventBus | None = None,
        *,
        health_callback: object | None = None,
        client_factory: object | None = None,
        session_store: BreezeSessionStore | None = None,
        data_directory: Path | None = None,
    ) -> None:
        """Initialize broker provider."""
        callback = health_callback if callable(health_callback) else None
        factory = client_factory if callable(client_factory) else None
        self.config = config
        self.config_provider = BreezeConfigurationProvider(config, credential_manager)
        self.factory = BrokerFactory(
            config,
            credential_manager,
            event_bus,
            client_factory=factory,
            session_store=session_store,
            data_directory=data_directory,
        )
        self.manager = BrokerManager(
            self.factory,
            config,
            event_bus,
            health_callback=callback,
        )

    def login_url(self) -> str:
        """Return Breeze OAuth login URL without loading SDK."""
        return login_url(self.config_provider.get_api_key() or "")

    @property
    def broker_service(self):
        """Return active broker instance (lazy)."""
        return self.manager.broker

    @property
    def broker(self):
        """Return active broker instance (lazy)."""
        return self.manager.broker

    def stop(self) -> None:
        """Stop broker manager."""
        self.manager.stop()
