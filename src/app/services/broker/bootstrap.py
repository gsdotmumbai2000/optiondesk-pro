"""Build broker integration bundle for dependency injection."""

from pathlib import Path

from app.brokers.bootstrap import BrokerProvider
from app.brokers.breeze.session_store import BreezeSessionStore
from app.config.models.app_config import BrokerConfig
from app.events.event_bus import EventBus
from app.security.credential_manager import CredentialManager
from app.services.broker.connection_status_service import ConnectionStatusService


def build_broker_bundle(
    config: BrokerConfig,
    credential_manager: CredentialManager,
    event_bus: EventBus | None,
    data_directory: Path,
) -> BrokerProvider:
    """Create broker provider with session persistence."""
    session_store = BreezeSessionStore(data_directory)
    provider = BrokerProvider(
        config,
        credential_manager,
        event_bus,
        session_store=session_store,
        data_directory=data_directory,
    )
    return provider


def build_connection_status_service(
    config: BrokerConfig,
    event_bus: EventBus | None,
) -> ConnectionStatusService:
    """Create connection status service."""
    return ConnectionStatusService(config, event_bus)
