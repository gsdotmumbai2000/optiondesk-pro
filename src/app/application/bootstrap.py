"""Application services layer bootstrap."""

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.commands.command_dispatcher import CommandDispatcher
from app.application.navigation.navigation_service import NavigationService
from app.application.orchestration.application_coordinator import ApplicationCoordinator
from app.application.registry.registry_factory import build_engine_registry
from app.application.orchestration.workspace_coordinator import WorkspaceCoordinator
from app.application.queries.query_dispatcher import QueryDispatcher
from app.application.services.ai_workspace_service import AIWorkspaceService
from app.application.services.backtesting_workspace_service import BacktestingWorkspaceService
from app.application.services.market_workspace_service import MarketWorkspaceService
from app.application.services.order_workspace_service import OrderWorkspaceService
from app.application.services.portfolio_workspace_service import PortfolioWorkspaceService
from app.application.services.broker_workspace_service import BrokerWorkspaceService
from app.application.services.settings_workspace_service import SettingsWorkspaceService
from app.application.services.strategy_workspace_service import StrategyWorkspaceService
from app.application.services.trading_workspace_service import TradingWorkspaceService
from app.application.session.session_manager import SessionManager
from app.application.validation.application_validator import ApplicationValidator
from app.brokers.bootstrap import BrokerProvider
from app.events.event_bus import EventBus
from app.live.bootstrap import LiveAnalyticsProvider
from app.market_data.bootstrap import MarketDataProvider
from app.services.broker.connection_status_service import ConnectionStatusService


class ApplicationProvider:
    """Wire application services layer dependencies."""

    def __init__(
        self,
        event_bus: EventBus | None = None,
        market_data: MarketDataProvider | None = None,
        broker_provider: BrokerProvider | None = None,
        connection_status: ConnectionStatusService | None = None,
    ) -> None:
        """Initialize application provider."""
        self.event_bus = event_bus
        self.engines = build_engine_registry(event_bus, market_data)
        self.validator = ApplicationValidator()
        self.cache = WorkspaceCache()
        self.sessions = SessionManager()
        self.market_data_service = market_data.service if market_data is not None else None
        self.live_analytics_provider = (
            LiveAnalyticsProvider(
                event_bus,
                self.market_data_service,
                self.engines,
                sessions=self.sessions,
                workspace_cache=self.cache,
            )
            if event_bus is not None and self.market_data_service is not None
            else None
        )
        self.live_analytics_service = (
            self.live_analytics_provider.service
            if self.live_analytics_provider is not None
            else None
        )
        if self.live_analytics_provider is not None:
            self.live_analytics_provider.start()

        self.trading = TradingWorkspaceService(
            self.engines,
            self.sessions,
            self.cache,
            self.market_data_service,
            self.live_analytics_service,
        )
        self.strategy = StrategyWorkspaceService(
            self.engines,
            self.sessions,
            self.cache,
            self.market_data_service,
            self.live_analytics_service,
        )
        self.portfolio = PortfolioWorkspaceService(
            self.engines,
            self.sessions,
            self.cache,
            self.market_data_service,
            self.live_analytics_service,
        )
        self.backtesting = BacktestingWorkspaceService(self.engines, self.sessions, self.cache)
        self.market = MarketWorkspaceService(
            self.engines,
            self.sessions,
            self.cache,
            self.market_data_service,
            self.live_analytics_service,
        )
        self.ai = AIWorkspaceService(
            self.engines,
            self.sessions,
            self.cache,
            self.market_data_service,
            self.live_analytics_service,
        )
        self.order = OrderWorkspaceService(self.engines, self.sessions, self.cache)
        self.settings = SettingsWorkspaceService(self.sessions)
        self.broker = (
            BrokerWorkspaceService(broker_provider, connection_status)
            if broker_provider is not None and connection_status is not None
            else None
        )

        self.workspaces = WorkspaceCoordinator(
            self.sessions,
            self.trading,
            self.strategy,
            self.portfolio,
            self.backtesting,
            self.market,
            self.ai,
            self.order,
            self.settings,
            event_bus,
        )
        self.coordinator = ApplicationCoordinator(
            self.engines,
            self.sessions,
            self.workspaces,
            self.cache,
            event_bus,
        )
        self.navigation = NavigationService(self.sessions, self.workspaces)
        self.commands = CommandDispatcher(
            self.validator,
            self.trading,
            self.strategy,
            self.portfolio,
            self.backtesting,
            self.market,
            self.ai,
        )
        self.queries = QueryDispatcher(
            self.validator,
            self.sessions,
            self.portfolio,
            self.strategy,
            self.market,
            self.ai,
        )
