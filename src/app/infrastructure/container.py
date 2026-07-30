"""Dependency injection container."""

from pathlib import Path

from dependency_injector import containers, providers

from app.config.configuration_manager import ConfigurationManager
from app.core.service_registry import ServiceRegistry
from app.events.event_bus import EventBus
from app.kernel.error_manager import ErrorManager
from app.kernel.health_monitor import HealthMonitor
from app.kernel.update_manager import UpdateManager
from app.kernel.version_manager import VersionManager
from app.kernel.workspace_manager import WorkspaceManager
from app.logging.logging_manager import LoggingManager
from app.market.bootstrap import MarketMasterProvider
from app.plugins.plugin_manager import PluginManager
from app.repositories.repository_factory import RepositoryFactory
from app.scheduler.scheduler_manager import SchedulerManager
from app.security.credential_manager import CredentialManager
from app.utils.runtime_paths import application_log_directory


def _data_directory(configuration_manager: ConfigurationManager) -> Path:
    """Resolve the application data directory from configuration."""
    return Path(configuration_manager.configuration.application.data_directory)


def _log_directory(configuration_manager: ConfigurationManager) -> Path:
    """Resolve the log directory from the application root."""
    _ = configuration_manager
    return application_log_directory()


def _workspace_directory(configuration_manager: ConfigurationManager) -> Path:
    """Resolve the workspace directory from configuration."""
    data_dir = configuration_manager.configuration.application.data_directory
    return Path(data_dir) / "workspaces"


def _plugin_directory(configuration_manager: ConfigurationManager) -> Path:
    """Resolve the plugin directory from configuration."""
    config = configuration_manager.configuration
    return Path(config.application.data_directory) / config.plugins.plugin_directory


class Container(containers.DeclarativeContainer):
    """Application dependency injection container."""

    configuration_manager = providers.Singleton(ConfigurationManager)

    version_manager = providers.Singleton(VersionManager)

    event_bus = providers.Singleton(EventBus)

    logging_manager = providers.Singleton(
        LoggingManager,
        config=configuration_manager.provided.configuration.provided.logging,
        log_directory=providers.Callable(_log_directory, configuration_manager),
    )

    service_registry = providers.Singleton(ServiceRegistry)

    scheduler_manager = providers.Singleton(
        SchedulerManager,
        timezone=configuration_manager.provided.configuration.provided.scheduler.provided.timezone,
    )

    repository_factory = providers.Singleton(
        RepositoryFactory,
        database_config=configuration_manager.provided.configuration.provided.database,
    )

    credential_manager = providers.Singleton(CredentialManager)

    workspace_manager = providers.Singleton(
        WorkspaceManager,
        workspace_directory=providers.Callable(
            _workspace_directory, configuration_manager
        ),
        event_bus=event_bus,
    )

    plugin_manager = providers.Singleton(
        PluginManager,
        plugin_directory=providers.Callable(_plugin_directory, configuration_manager),
        event_bus=event_bus,
        version_manager=version_manager,
    )

    health_monitor = providers.Singleton(
        HealthMonitor,
        event_bus=event_bus,
        repository_factory=repository_factory,
        scheduler_manager=scheduler_manager,
        plugin_registry=plugin_manager.provided.registry,
    )

    error_manager = providers.Singleton(ErrorManager, logging_manager=logging_manager)

    update_manager = providers.Singleton(
        UpdateManager,
        application_config=configuration_manager.provided.configuration.provided.application,
        version_manager=version_manager,
    )

    market_master_provider = providers.Singleton(
        MarketMasterProvider,
        data_directory=providers.Callable(_data_directory, configuration_manager),
        event_bus=event_bus,
    )
