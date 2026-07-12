"""Workspace coordinator."""

from app.application.events import WorkspaceClosedEvent, WorkspaceOpenedEvent
from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceView
from app.application.services.ai_workspace_service import AIWorkspaceService
from app.application.services.backtesting_workspace_service import BacktestingWorkspaceService
from app.application.services.market_workspace_service import MarketWorkspaceService
from app.application.services.order_workspace_service import OrderWorkspaceService
from app.application.services.portfolio_workspace_service import PortfolioWorkspaceService
from app.application.services.settings_workspace_service import SettingsWorkspaceService
from app.application.services.strategy_workspace_service import StrategyWorkspaceService
from app.application.services.trading_workspace_service import TradingWorkspaceService
from app.application.session.session_manager import SessionManager
from app.events.event_bus import EventBus


class WorkspaceCoordinator:
    """Coordinate workspace open/close and routing."""

    def __init__(
        self,
        sessions: SessionManager,
        trading: TradingWorkspaceService,
        strategy: StrategyWorkspaceService,
        portfolio: PortfolioWorkspaceService,
        backtesting: BacktestingWorkspaceService,
        market: MarketWorkspaceService,
        ai: AIWorkspaceService,
        order: OrderWorkspaceService,
        settings: SettingsWorkspaceService,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize coordinator."""
        self._sessions = sessions
        self._trading = trading
        self._strategy = strategy
        self._portfolio = portfolio
        self._backtesting = backtesting
        self._market = market
        self._ai = ai
        self._order = order
        self._settings = settings
        self._event_bus = event_bus

    def open_workspace(
        self,
        session_id: str,
        workspace: WorkspaceType,
        entity_id: str = "",
    ) -> WorkspaceView:
        """Open workspace and publish event."""
        self._sessions.set_active_workspace(session_id, workspace, entity_id)
        view = self.get_view(session_id, workspace)
        self._publish_opened(session_id, workspace)
        return view

    def close_workspace(self, session_id: str, workspace: WorkspaceType) -> None:
        """Close workspace and publish event."""
        if self._event_bus is not None:
            self._event_bus.publish(
                WorkspaceClosedEvent(
                    payload={"session_id": session_id, "workspace": workspace.value}
                )
            )

    def get_view(self, session_id: str, workspace: WorkspaceType) -> WorkspaceView:
        """Return workspace view by type."""
        views = {
            WorkspaceType.TRADING: self._trading.view,
            WorkspaceType.STRATEGY: self._strategy.view,
            WorkspaceType.PORTFOLIO: self._portfolio.view,
            WorkspaceType.BACKTESTING: self._backtesting.view,
            WorkspaceType.MARKET: self._market.view,
            WorkspaceType.AI: self._ai.view,
            WorkspaceType.ORDER: self._order.view,
            WorkspaceType.SETTINGS: self._settings.view,
        }
        return views[workspace](session_id)

    def _publish_opened(self, session_id: str, workspace: WorkspaceType) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            WorkspaceOpenedEvent(
                payload={"session_id": session_id, "workspace": workspace.value}
            )
        )
