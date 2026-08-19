"""Workspace shell widgets."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QWidget

from app.ui.ai.ai_view import AIView
from app.ui.backtesting.backtest_view import BacktestView
from app.ui.market.market_view import MarketView
from app.ui.monitor.monitor_view import MonitorView
from app.ui.portfolio.portfolio_view import PortfolioView
from app.ui.reports.reports_view import ReportsView
from app.ui.settings.settings_view import SettingsView
from app.ui.strategy.strategy_builder_view import StrategyBuilderView
from app.ui.widgets.common import style_splitter_handle
from app.ui.viewmodels.ai_viewmodel import AIViewModel
from app.ui.viewmodels.backtesting_viewmodel import BacktestingViewModel
from app.ui.viewmodels.market_viewmodel import MarketViewModel
from app.ui.viewmodels.monitor_viewmodel import MonitorViewModel
from app.ui.viewmodels.portfolio_viewmodel import PortfolioViewModel
from app.ui.viewmodels.reports_viewmodel import ReportsViewModel
from app.ui.viewmodels.settings_viewmodel import SettingsViewModel
from app.ui.viewmodels.strategy_viewmodel import StrategyViewModel
from app.ui.viewmodels.trading_viewmodel import TradingViewModel


def trading_workspace(vm: TradingViewModel, monitor_vm: MonitorViewModel) -> QWidget:
    """Trading workspace with strategy builder and monitor panel.

    A QSplitter, not a plain stacked QVBoxLayout: both child views have
    their own tables that want real room to grow (the leg table; Monitor's
    alerts/warnings/recommendations), and a fixed stack forces them to
    permanently share space in whatever proportion their default sizeHints
    happen to produce. The splitter gives the builder most of the space by
    default while staying user-resizable -- drag the handle to see more of
    either side."""
    splitter = QSplitter(Qt.Orientation.Vertical)
    splitter.addWidget(StrategyBuilderView(vm))
    splitter.addWidget(MonitorView(monitor_vm))
    splitter.setStretchFactor(0, 3)
    splitter.setStretchFactor(1, 1)
    style_splitter_handle(splitter)
    return splitter


def market_workspace(vm: MarketViewModel) -> QWidget:
    return MarketView(vm)


def strategy_workspace(vm: StrategyViewModel) -> QWidget:
    from app.ui.strategy.strategy_list_view import StrategyListView

    return StrategyListView(vm)


def portfolio_workspace(vm: PortfolioViewModel) -> QWidget:
    return PortfolioView(vm)


def backtesting_workspace(vm: BacktestingViewModel) -> QWidget:
    return BacktestView(vm)


def ai_workspace(vm: AIViewModel) -> QWidget:
    return AIView(vm)


def reports_workspace(vm: ReportsViewModel) -> QWidget:
    return ReportsView(vm)


def settings_workspace(vm: SettingsViewModel) -> QWidget:
    return SettingsView(vm)
