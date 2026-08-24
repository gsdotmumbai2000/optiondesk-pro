"""OptionDesk Pro main window."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication, QMainWindow, QStatusBar, QStyle, QSystemTrayIcon, QTabWidget

from app.ui.dialogs.broker_login_dialog import BrokerLoginDialog
from app.ui.dialogs.broker_settings_dialog import BrokerSettingsDialog
from app.ui.docking.dock_manager import DockManager
from app.ui.notifications.desktop_toast_channel import DesktopToastChannel
from app.ui.widgets.connection_indicator import ConnectionIndicator
from app.ui.widgets.market_status_indicator import MarketStatusIndicator
from app.ui.widgets.recording_indicator import RecordingIndicator
from app.ui.main_window.ribbon_bar import build_ribbon
from app.ui.models.ui_enums import UIWorkspaceId
from app.ui.navigation.navigation_pane import NavigationPane
from app.ui.themes.theme_manager import ThemeManager
from app.ui.viewmodels import (
    AIViewModel,
    BacktestingViewModel,
    BrokerViewModel,
    MarketViewModel,
    MonitorViewModel,
    PortfolioViewModel,
    ReportsViewModel,
    SettingsViewModel,
    StrategyViewModel,
    TradingViewModel,
    ViewModelContext,
)
from app.ui.workspaces.workspace_factory import (
    ai_workspace,
    backtesting_workspace,
    market_workspace,
    portfolio_workspace,
    reports_workspace,
    settings_workspace,
    strategy_workspace,
    trading_workspace,
)


class MainWindow(QMainWindow):
    """Professional desktop shell with ribbon, docks, and workspace tabs."""

    def __init__(
        self,
        ctx: ViewModelContext,
        theme_manager: ThemeManager | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._ctx = ctx
        self._theme_manager = theme_manager or ThemeManager()
        self.setWindowTitle("OptionDesk Pro")
        self.resize(1440, 900)
        self._build_viewmodels()
        self._build_menu()
        self._build_ribbon()
        self._build_central()
        self._build_docks()
        self._build_status()
        self._build_notifications()
        self._wire_navigation()
        self._wire_events()

    def _wire_events(self) -> None:
        self._ctx.events.strategy_updated.connect(self._trading_vm.on_strategy_updated)

    def _build_viewmodels(self) -> None:
        self._trading_vm = TradingViewModel(self._ctx, self)
        self._market_vm = MarketViewModel(self._ctx, self)
        self._strategy_vm = StrategyViewModel(self._ctx, self)
        self._portfolio_vm = PortfolioViewModel(self._ctx, self)
        self._backtest_vm = BacktestingViewModel(self._ctx, self)
        self._ai_vm = AIViewModel(self._ctx, self)
        self._reports_vm = ReportsViewModel(self._ctx, self)
        self._settings_vm = SettingsViewModel(self._ctx, self._theme_manager, self)
        self._monitor_vm = MonitorViewModel(self._ctx, self)
        self._broker_vm = BrokerViewModel(self._ctx, self)

    def _build_menu(self) -> None:
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        file_menu.addAction("E&xit", self.close)
        view_menu = menu.addMenu("&View")
        fullscreen = QAction("Toggle &Fullscreen", self)
        fullscreen.setShortcut(QKeySequence(Qt.Key.Key_F11))
        fullscreen.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen)
        theme_action = QAction("Cycle &Theme", self)
        theme_action.triggered.connect(self._settings_vm.apply_theme_command.execute)
        view_menu.addAction(theme_action)
        broker_menu = menu.addMenu("&Broker")
        broker_menu.addAction("Login...", self._show_broker_login)
        broker_menu.addAction("Settings...", self._show_broker_settings)
        broker_menu.addAction("Reconnect", self._broker_vm.reconnect_command.execute)
        broker_menu.addAction("Logout", self._broker_vm.logout_command.execute)

    def _build_ribbon(self) -> None:
        self.addToolBar(build_ribbon(self, self._trading_vm, self._backtest_vm))

    def _build_central(self) -> None:
        self._nav = NavigationPane(self)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self._create_nav_toolbar())
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._workspace_map = {
            UIWorkspaceId.TRADING: trading_workspace(self._trading_vm, self._monitor_vm),
            UIWorkspaceId.MARKET: market_workspace(self._market_vm),
            UIWorkspaceId.STRATEGY: strategy_workspace(self._strategy_vm),
            UIWorkspaceId.PORTFOLIO: portfolio_workspace(self._portfolio_vm),
            UIWorkspaceId.BACKTESTING: backtesting_workspace(self._backtest_vm),
            UIWorkspaceId.AI: ai_workspace(self._ai_vm),
            UIWorkspaceId.REPORTS: reports_workspace(self._reports_vm),
            UIWorkspaceId.SETTINGS: settings_workspace(self._settings_vm),
        }
        for ws_id, widget in self._workspace_map.items():
            self._tabs.addTab(widget, ws_id.value.replace("_", " ").title())
        self.setCentralWidget(self._tabs)

    def _create_nav_toolbar(self):
        from PySide6.QtWidgets import QToolBar

        bar = QToolBar("Navigation", self)
        bar.setMovable(False)
        bar.addWidget(self._nav)
        return bar

    def _build_docks(self) -> None:
        DockManager(self).add_monitor_dock(self._monitor_vm)

    def _build_status(self) -> None:
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._connection_indicator = ConnectionIndicator(self)
        self._market_status_indicator = MarketStatusIndicator(self)
        self._recording_indicator = RecordingIndicator(self)
        self._last_tick_time = "—"
        self._status.addPermanentWidget(self._connection_indicator)
        self._status.addPermanentWidget(self._market_status_indicator)
        self._status.addPermanentWidget(self._recording_indicator)
        self._broker_vm.status_changed.connect(self._on_broker_status)
        self._market_vm.market_status_changed.connect(self._on_market_status_bar)
        self._market_vm.tick_updated.connect(self._on_tick_status_bar)
        self._ctx.events.recording_tick_captured.connect(self._on_recording_tick)
        self._broker_vm.refresh_status()
        self._market_vm.refresh()
        self._init_recording_indicator()
        for vm in (
            self._trading_vm,
            self._market_vm,
            self._portfolio_vm,
            self._ai_vm,
            self._broker_vm,
        ):
            vm.status_message_changed.connect(self._status.showMessage)

    def _build_notifications(self) -> None:
        """Wire a real alert-delivery channel: a desktop tray toast, shown
        for every alert MonitorProvider's AlertService raises from here on.
        Skipped (notification_service keeps its build-only default) when no
        system tray is available -- e.g. some CI/remote-desktop sessions --
        so this never blocks startup or raises there."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        icon = self.windowIcon()
        if icon.isNull():
            icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
        self._tray_icon = QSystemTrayIcon(icon, self)
        self._tray_icon.setToolTip("OptionDesk Pro")
        self._tray_icon.show()
        channel = DesktopToastChannel(self._tray_icon)
        self._ctx.provider.engines.monitor.notification_service.set_channel(channel)

    def _on_broker_status(self, payload: dict) -> None:
        status = payload.get("status")
        if not isinstance(status, object):
            return
        self._connection_indicator.update_status(
            str(payload.get("broker_name", "Broker")),
            status,
            str(payload.get("user_id", "")),
            str(payload.get("environment", "")),
        )
        self._update_market_status_bar()

    def _on_market_status_bar(self, payload: dict) -> None:
        self._update_market_status_bar(payload)

    def _on_tick_status_bar(self, payload: dict) -> None:
        tick = payload.get("tick", payload)
        self._last_tick_time = str(tick.get("timestamp", "—"))
        self._update_market_status_bar()

    def _update_market_status_bar(self, payload: dict | None = None) -> None:
        market = "—"
        connected = "—"
        last_tick = getattr(self, "_last_tick_time", "—")
        if payload:
            market = str(payload.get("status", market))
            connected = str(payload.get("connection", connected))
            last_tick = str(payload.get("last_tick", last_tick))
        elif hasattr(self, "_market_vm"):
            market = self._market_vm.market_status
            connected = self._market_vm.connection_status
            last_tick = self._market_vm.last_update
        self._market_status_indicator.update_status(market, last_tick, connected)

    def _init_recording_indicator(self) -> None:
        """Show the badge immediately if recording started before the UI existed.

        TickRecorder.start() (and its one-shot start signal, if it fired one)
        runs during kernel initialize(), before MainWindow/UIEventBridge
        exist, so the initial state has to be pulled here rather than
        pushed via an event the bridge would have missed.
        """
        recorder = self._ctx.provider.tick_recorder
        if recorder is not None:
            self._recording_indicator.set_recording(True, recorder.tick_count)

    def _on_recording_tick(self, payload: dict) -> None:
        self._recording_indicator.set_recording(True, int(payload.get("tick_count", 0)))

    def _show_broker_login(self) -> None:
        dialog = BrokerLoginDialog(self._broker_vm, self)
        dialog.exec()

    def _show_broker_settings(self) -> None:
        dialog = BrokerSettingsDialog(self._broker_vm, self)
        dialog.exec()

    def _wire_navigation(self) -> None:
        self._workspace_tab_index = {ws.value: i for i, ws in enumerate(UIWorkspaceId)}
        self._nav.workspace_selected.connect(self._activate_workspace_tab)
        self._strategy_vm.workspace_switch_requested.connect(self._activate_workspace_tab)

    def _activate_workspace_tab(self, workspace_id: str) -> None:
        index = self._workspace_tab_index.get(workspace_id)
        if index is not None:
            self._tabs.setCurrentIndex(index)

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
