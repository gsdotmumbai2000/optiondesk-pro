"""Broker integration bootstrap."""

from app.brokers.broker_factory.factory import BrokerFactory
from app.brokers.broker_manager.manager import BrokerManager
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
    ) -> None:
        """Initialize broker provider."""
        callback = health_callback if callable(health_callback) else None
        factory = client_factory if callable(client_factory) else None
        self.factory = BrokerFactory(
            config,
            credential_manager,
            event_bus,
            client_factory=factory,
        )
        self.manager = BrokerManager(
            self.factory,
            config,
            event_bus,
            health_callback=callback,
        )
        self.broker_service = self.manager.broker

    def stop(self) -> None:
        """Stop broker manager."""
        self.manager.stop()
