"""Application kernel."""

from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.config.configuration_manager import ConfigurationManager
from app.core.service_registry import ServiceRegistry
from app.events.application_events import (ApplicationShuttingDownEvent,
                                           ApplicationStartedEvent,
                                           ApplicationStoppedEvent)
from app.events.event_bus import EventBus
from app.exceptions.global_exception_handler import GlobalExceptionHandler
from app.infrastructure.container import Container
from app.kernel.error_manager import ErrorManager
from app.kernel.health_monitor import HealthMonitor
from app.kernel.update_manager import UpdateManager
from app.kernel.version_manager import VersionManager
from app.kernel.workspace_manager import WorkspaceManager
from app.logging.logging_manager import LoggingManager, get_logger
from app.market.bootstrap import MarketMasterProvider
from app.plugins.plugin_manager import PluginManager
from app.repositories.repository_factory import RepositoryFactory
from app.scheduler.scheduler_manager import SchedulerManager
from app.security.credential_manager import CredentialManager
from app.services.service_keys import ServiceKeys
from app.ui.application import create_application
from app.utils.constants import LOG_DIR_NAME
from app.utils.file_helper import FileHelper
from app.utils.thread_helper import ThreadHelper

logger = get_logger(__name__)


class ApplicationKernel:
    """Central application orchestrator and lifecycle manager."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize the application kernel."""
        self._container = Container()
        self._config_dir = config_dir
        self._qt_application: QApplication | None = None
        self._thread_helper = ThreadHelper()
        self._running = False
        self._initialized = False

        self.configuration_manager: ConfigurationManager | None = None
        self.logging_manager: LoggingManager | None = None
        self.service_registry: ServiceRegistry | None = None
        self.event_bus: EventBus | None = None
        self.scheduler_manager: SchedulerManager | None = None
        self.plugin_manager: PluginManager | None = None
        self.repository_factory: RepositoryFactory | None = None
        self.workspace_manager: WorkspaceManager | None = None
        self.health_monitor: HealthMonitor | None = None
        self.exception_handler: GlobalExceptionHandler | None = None
        self.update_manager: UpdateManager | None = None
        self.error_manager: ErrorManager | None = None
        self.version_manager: VersionManager | None = None
        self.credential_manager: CredentialManager | None = None
        self.market_master_provider: MarketMasterProvider | None = None

    def initialize(self) -> None:
        """Initialize all application subsystems."""
        if self._initialized:
            return

        self._bootstrap_configuration()
        self._bootstrap_logging()
        self._bootstrap_versioning()
        self._bootstrap_exception_handling()
        self._resolve_dependencies()
        self._start_subsystems()
        self._initialized = True
        logger.info("Application kernel initialized")

    def start(self) -> int:
        """Start the application event loop."""
        if not self._initialized:
            self.initialize()

        assert self.service_registry is not None
        assert self.event_bus is not None
        assert self.version_manager is not None
        assert self.workspace_manager is not None

        self.service_registry.initialize_all()
        self.service_registry.start_all()
        self.workspace_manager.load_active_profile()

        self._qt_application = create_application()
        self._running = True
        self.event_bus.publish(
            ApplicationStartedEvent(
                payload={"version": self.version_manager.application_version}
            )
        )
        logger.info("Application started")
        return self._qt_application.exec()

    def stop(self) -> None:
        """Request application stop."""
        self.shutdown()
        if self._qt_application is not None:
            self._qt_application.quit()

    def restart(self) -> None:
        """Restart the application."""
        self.shutdown()
        self.initialize()
        self.start()

    def shutdown(self) -> None:
        """Shutdown all subsystems gracefully."""
        if self.event_bus is not None:
            self.event_bus.publish(ApplicationShuttingDownEvent())

        self._thread_helper.shutdown()

        if self.workspace_manager is not None:
            self.workspace_manager.save_active_profile()
        if self.service_registry is not None:
            self.service_registry.stop_all()
        if self.scheduler_manager is not None:
            self.scheduler_manager.stop()
        if self.plugin_manager is not None:
            self.plugin_manager.unload_all()
        if self.repository_factory is not None:
            self.repository_factory.close()
        if self.market_master_provider is not None:
            self.market_master_provider.shutdown()
        if self.health_monitor is not None:
            self.health_monitor.stop()
        if self.event_bus is not None:
            self.event_bus.publish(ApplicationStoppedEvent())
            self.event_bus.stop()
        if self.logging_manager is not None:
            self.logging_manager.shutdown()
        if self.exception_handler is not None:
            self.exception_handler.uninstall()

        self._running = False
        self._initialized = False
        logger.info("Application kernel shutdown complete")

    def _bootstrap_configuration(self) -> None:
        """Load and validate configuration."""
        self.configuration_manager = ConfigurationManager(self._config_dir)
        self.configuration_manager.load()

        data_dir = Path(
            self.configuration_manager.configuration.application.data_directory
        )
        user_config_dir = data_dir / "config"
        self.configuration_manager.set_user_config_dir(user_config_dir)
        self.configuration_manager.load()
        self.configuration_manager.validate()
        FileHelper.ensure_directory(data_dir)

        self._container.configuration_manager.override(self.configuration_manager)

    def _bootstrap_logging(self) -> None:
        """Initialize logging."""
        assert self.configuration_manager is not None
        log_dir = (
            Path(self.configuration_manager.configuration.application.data_directory)
            / LOG_DIR_NAME
        )
        FileHelper.ensure_directory(log_dir)
        self.logging_manager = self._container.logging_manager()
        self.logging_manager.initialize()

    def _bootstrap_versioning(self) -> None:
        """Initialize version manager."""
        self.version_manager = self._container.version_manager()
        self.version_manager.load()
        self.version_manager.check_compatibility()

    def _bootstrap_exception_handling(self) -> None:
        """Install global exception handler."""
        assert self.logging_manager is not None
        self.exception_handler = GlobalExceptionHandler(self.logging_manager)
        self.exception_handler.install()

    def _resolve_dependencies(self) -> None:
        """Resolve components from the DI container."""
        self.service_registry = self._container.service_registry()
        self.event_bus = self._container.event_bus()
        self.scheduler_manager = self._container.scheduler_manager()
        self.repository_factory = self._container.repository_factory()
        self.credential_manager = self._container.credential_manager()
        self.workspace_manager = self._container.workspace_manager()
        self.plugin_manager = self._container.plugin_manager()
        self.health_monitor = self._container.health_monitor()
        self.error_manager = self._container.error_manager()
        self.update_manager = self._container.update_manager()
        self.market_master_provider = self._container.market_master_provider()
        self._register_services()

    def _start_subsystems(self) -> None:
        """Start core subsystems."""
        assert self.event_bus is not None
        assert self.repository_factory is not None
        assert self.scheduler_manager is not None
        assert self.plugin_manager is not None
        assert self.health_monitor is not None
        assert self.update_manager is not None

        self.event_bus.start()
        self.repository_factory.initialize()
        self.scheduler_manager.start()
        self.plugin_manager.discover_and_load()
        self.health_monitor.start()
        self.update_manager.check_for_updates_async()

    def _register_services(self) -> None:
        """Register core services in the service registry."""
        assert self.service_registry is not None
        self.service_registry.register("event_bus", lambda: self.event_bus)
        self.service_registry.register(
            "configuration_manager",
            lambda: self.configuration_manager,
        )
        self.service_registry.register(
            "repository_factory",
            lambda: self.repository_factory,
        )
        assert self.market_master_provider is not None
        provider = self.market_master_provider
        self.service_registry.register(ServiceKeys.MARKET_MASTER, lambda: provider)
        self.service_registry.register(
            ServiceKeys.INSTRUMENT,
            lambda: provider.instrument_service,
        )
        self.service_registry.register(
            ServiceKeys.MARKET_CALENDAR,
            lambda: provider.calendar_service,
        )
        self.service_registry.register(
            ServiceKeys.EXPIRY, lambda: provider.expiry_service
        )
        self.service_registry.register(
            ServiceKeys.HOLIDAY,
            lambda: provider.holiday_service,
        )
        self.service_registry.register(
            ServiceKeys.TRADING_SESSION,
            lambda: provider.session_service,
        )
