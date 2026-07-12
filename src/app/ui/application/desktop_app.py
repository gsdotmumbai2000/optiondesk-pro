"""Desktop application bootstrap."""

from app.application.bootstrap import ApplicationProvider
from app.brokers.bootstrap import BrokerProvider
from app.events.event_bus import EventBus
from app.services.broker.connection_status_service import ConnectionStatusService
from app.ui.application.qt_application import create_application
from app.ui.application.worker_pool import BackgroundWorker
from app.ui.events.ui_event_bridge import UIEventBridge
from app.ui.main_window.main_window import MainWindow
from app.ui.models.ui_enums import UITheme
from app.ui.themes.theme_manager import ThemeManager
from app.ui.viewmodels.context import ViewModelContext


class DesktopApplication:
    """Wire UI shell to Application Services Layer."""

    def __init__(
        self,
        event_bus: EventBus | None = None,
        broker_provider: BrokerProvider | None = None,
        connection_status: ConnectionStatusService | None = None,
    ) -> None:
        """Initialize desktop application."""
        self._event_bus = event_bus
        self._provider = ApplicationProvider(
            event_bus=event_bus,
            broker_provider=broker_provider,
            connection_status=connection_status,
        )
        self._theme = ThemeManager()
        self._worker = BackgroundWorker()
        self._main_window: MainWindow | None = None

    @property
    def provider(self) -> ApplicationProvider:
        """Return application provider."""
        return self._provider

    def run(self) -> int:
        """Create Qt app, show main window, run event loop."""
        app = create_application()
        self._main_window = self._create_main_window()
        self._restore_broker_session()
        self._main_window.show()
        return app.exec()

    def show(self) -> MainWindow:
        """Show main window without starting event loop."""
        create_application()
        self._main_window = self._create_main_window()
        self._restore_broker_session()
        self._main_window.show()
        return self._main_window

    def _create_main_window(self) -> MainWindow:
        """Build main window with shared theme and session context."""
        self._theme.apply(UITheme.DARK)
        session = self._provider.coordinator.start_session()
        ctx = ViewModelContext(
            provider=self._provider,
            worker=self._worker,
            events=UIEventBridge(self._provider.event_bus),
            session_id=session.session_id,
        )
        return MainWindow(ctx, theme_manager=self._theme)

    def _restore_broker_session(self) -> None:
        """Attempt broker session restore after restart."""
        broker = self._provider.broker
        if broker is None:
            return
        try:
            broker.restore_session()
        except Exception:
            pass
