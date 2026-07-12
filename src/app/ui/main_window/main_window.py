"""OptionDesk Pro main window."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow, QStatusBar, QTabWidget

from app.ui.dialogs.broker_login_dialog import BrokerLoginDialog
from app.ui.dialogs.broker_settings_dialog import BrokerSettingsDialog
from app.ui.docking.dock_manager import DockManager
from app.ui.widgets.connection_indicator import ConnectionIndicator
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
        self._status.addPermanentWidget(self._connection_indicator)
        self._broker_vm.status_changed.connect(self._on_broker_status)
        self._broker_vm.refresh_status()
        for vm in (
            self._trading_vm,
            self._market_vm,
            self._portfolio_vm,
            self._ai_vm,
            self._broker_vm,
        ):
            vm.status_message_changed.connect(self._status.showMessage)

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

    def _show_broker_login(self) -> None:
        dialog = BrokerLoginDialog(self._broker_vm, self)
        dialog.exec()

    def _show_broker_settings(self) -> None:
        dialog = BrokerSettingsDialog(self._broker_vm, self)
        dialog.exec()

    def _wire_navigation(self) -> None:
        index_map = {ws: i for i, ws in enumerate(UIWorkspaceId)}
        self._nav.workspace_selected.connect(
            lambda name: self._tabs.setCurrentIndex(index_map[UIWorkspaceId(name)])
        )

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
