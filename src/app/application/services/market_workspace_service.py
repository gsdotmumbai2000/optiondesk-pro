"""Market workspace service."""

from datetime import datetime, timezone

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult, WorkspaceView
from app.application.registry.engine_registry import EngineRegistry
from app.application.session.session_manager import SessionManager
from app.market_data.models.snapshot import MarketSnapshot


class MarketWorkspaceService:
    """Market data workspace API for UI."""

    def __init__(
        self,
        engines: EngineRegistry,
        sessions: SessionManager,
        cache: WorkspaceCache,
    ) -> None:
        """Initialize service."""
        self._engines = engines
        self._sessions = sessions
        self._cache = cache
        self._watchlists: dict[str, tuple[str, ...]] = {}

    def refresh_market(self, session_id: str) -> WorkspaceOperationResult:
        """Refresh market data via market data engine."""
        engine = self._engines.market_data
        if engine is None:
            return WorkspaceOperationResult(
                False,
                WorkspaceType.MARKET,
                "Market data engine not configured",
            )
        self._cache.put_data(f"{session_id}:market", {"refreshed": True})
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            "Market data refresh initiated",
        )

    def watchlist(self, session_id: str, symbols: tuple[str, ...]) -> WorkspaceOperationResult:
        """Set watchlist symbols."""
        self._watchlists[session_id] = symbols
        self._cache.put_data(f"{session_id}:watchlist", symbols)
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            f"Watchlist updated ({len(symbols)} symbols)",
            symbols,
        )

    def market_overview(self, session_id: str) -> WorkspaceOperationResult:
        """Return market overview from cache or master."""
        cached = self._cache.get_data(f"{session_id}:market")
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            "Market overview",
            cached,
        )

    def option_chain(self, session_id: str, symbol: str) -> WorkspaceOperationResult:
        """Return option chain context (framework)."""
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            f"Option chain for {symbol}",
            self._cache.get_data(f"{session_id}:chain:{symbol}"),
        )

    def market_scanner(self, session_id: str) -> WorkspaceOperationResult:
        """Return scanner results (framework)."""
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            "Market scanner results",
            self._cache.get_data(f"{session_id}:scanner"),
        )

    def volatility_dashboard(self, session_id: str) -> WorkspaceOperationResult:
        """Return volatility dashboard data (framework)."""
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            "Volatility dashboard",
            self._cache.get_data(f"{session_id}:volatility"),
        )

    def cache_snapshot(self, session_id: str, snapshot: MarketSnapshot) -> None:
        """Cache market snapshot for UI queries."""
        self._cache.put_data(f"{session_id}:snapshot", snapshot)

    def view(self, session_id: str) -> WorkspaceView:
        """Return market workspace view."""
        symbols = self._watchlists.get(session_id, ())
        return WorkspaceView(
            workspace=WorkspaceType.MARKET,
            title="Market Workspace",
            summary=f"Watchlist: {len(symbols)} symbols",
            entity_id="",
            updated_at=datetime.now(timezone.utc),
        )
