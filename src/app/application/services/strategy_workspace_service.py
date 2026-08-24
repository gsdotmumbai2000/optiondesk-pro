"""Strategy workspace service."""

from datetime import datetime, timezone

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult, WorkspaceView
from app.application.ports.live_analytics_port import LiveAnalyticsPort
from app.application.ports.market_data_port import MarketDataPort
from app.application.registry.engine_registry import EngineRegistry
from app.application.services.live_analytics_support import LiveAnalyticsSupport
from app.application.services.market_data_support import MarketDataSupport
from app.application.session.session_manager import SessionManager
from app.strategy.models.strategy import Strategy


class StrategyWorkspaceService(MarketDataSupport, LiveAnalyticsSupport):
    """Strategy CRUD and template workspace API."""

    def __init__(
        self,
        engines: EngineRegistry,
        sessions: SessionManager,
        cache: WorkspaceCache,
        market_data: MarketDataPort | None = None,
        live_analytics: LiveAnalyticsPort | None = None,
    ) -> None:
        """Initialize service."""
        MarketDataSupport.__init__(self, market_data)
        LiveAnalyticsSupport.__init__(self, live_analytics)
        self._engines = engines
        self._sessions = sessions
        self._cache = cache

    def load_strategy(
        self,
        session_id: str,
        strategy_id: str,
    ) -> WorkspaceOperationResult:
        """Load strategy by id."""
        strategy = self._engines.strategy.repository.get(strategy_id)
        if strategy is None:
            return WorkspaceOperationResult(
                False,
                WorkspaceType.STRATEGY,
                f"Strategy not found: {strategy_id}",
            )
        self._cache.put_strategy(strategy_id, strategy)
        self._sessions.add_recent_strategy(session_id, strategy_id, strategy.metadata.name)
        self._sessions.set_active_workspace(session_id, WorkspaceType.STRATEGY, strategy_id)
        return WorkspaceOperationResult(
            True,
            WorkspaceType.STRATEGY,
            "Strategy loaded",
            strategy,
        )

    def save_strategy(
        self,
        session_id: str,
        strategy: Strategy,
    ) -> WorkspaceOperationResult:
        """Save strategy."""
        saved = self._engines.strategy.service.update(strategy)
        self._cache.put_strategy(saved.strategy_id, saved)
        self._sessions.add_recent_strategy(session_id, saved.strategy_id, saved.metadata.name)
        return WorkspaceOperationResult(
            True,
            WorkspaceType.STRATEGY,
            "Strategy saved",
            saved,
        )

    def create_strategy(self, session_id: str, strategy: Strategy) -> WorkspaceOperationResult:
        """Create new strategy."""
        created = self._engines.strategy.service.create(strategy)
        self._cache.put_strategy(created.strategy_id, created)
        self._sessions.set_active_workspace(
            session_id,
            WorkspaceType.STRATEGY,
            created.strategy_id,
        )
        return WorkspaceOperationResult(
            True,
            WorkspaceType.STRATEGY,
            "Strategy created",
            created,
        )

    def delete_strategy(self, session_id: str, strategy_id: str) -> WorkspaceOperationResult:
        """Delete strategy by id."""
        deleted = self._engines.strategy.service.delete(strategy_id)
        if not deleted:
            return WorkspaceOperationResult(
                False,
                WorkspaceType.STRATEGY,
                f"Strategy not found: {strategy_id}",
            )
        self._cache.invalidate(strategy_id)
        return WorkspaceOperationResult(
            True,
            WorkspaceType.STRATEGY,
            "Strategy deleted",
        )

    def list_strategies(self, session_id: str) -> WorkspaceOperationResult:
        """List all strategies."""
        strategies = self._engines.strategy.repository.list_all()
        return WorkspaceOperationResult(
            True,
            WorkspaceType.STRATEGY,
            f"{len(strategies)} strategies",
            strategies,
        )

    def get_strategy(self, strategy_id: str):
        """Return strategy by id."""
        return self._engines.strategy.repository.get(strategy_id)

    def view(self, session_id: str) -> WorkspaceView:
        """Return strategy workspace view."""
        session = self._sessions.get(session_id)
        count = len(self._engines.strategy.repository.list_all())
        return WorkspaceView(
            workspace=WorkspaceType.STRATEGY,
            title="Strategy Workspace",
            summary=f"{count} strategies, {len(session.recent_strategies)} recent",
            entity_id="",
            updated_at=datetime.now(timezone.utc),
        )

    def underlying_price(self, symbol: str, exchange: str = "NSE") -> WorkspaceOperationResult:
        """Return live underlying price for strategy context."""
        price = self.latest_price(symbol, exchange)
        return WorkspaceOperationResult(
            price is not None,
            WorkspaceType.STRATEGY,
            f"Price for {symbol}",
            {"symbol": symbol, "exchange": exchange, "price": str(price or "")},
        )

    def live_chain_context(
        self,
        symbol: str,
        exchange: str = "NSE",
        expiry_date: str = "",
    ) -> WorkspaceOperationResult:
        """Return live option chain for strategy evaluation."""
        chain = self.live_option_chain(symbol, exchange, expiry_date)
        payload = chain.model_dump(mode="json") if chain is not None else {}
        return WorkspaceOperationResult(
            chain is not None,
            WorkspaceType.STRATEGY,
            f"Live chain for {symbol}",
            payload,
        )
