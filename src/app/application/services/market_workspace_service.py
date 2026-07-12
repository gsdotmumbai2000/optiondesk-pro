"""Market workspace service."""

from datetime import datetime, timezone

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult, WorkspaceView
from app.application.registry.engine_registry import EngineRegistry
from app.application.session.session_manager import SessionManager
from app.brokers.shared.enums import ProductType
from app.market_data.models.snapshot import MarketSnapshot
from app.market_data.services.market_data_service import MarketDataService


class MarketWorkspaceService:
    """Market data workspace API for UI."""

    def __init__(
        self,
        engines: EngineRegistry,
        sessions: SessionManager,
        cache: WorkspaceCache,
        market_data: MarketDataService | None = None,
    ) -> None:
        """Initialize service."""
        self._engines = engines
        self._sessions = sessions
        self._cache = cache
        self._market_data = market_data or self._resolve_market_data()
        self._watchlists: dict[str, tuple[str, ...]] = {}

    def refresh_market(self, session_id: str) -> WorkspaceOperationResult:
        """Refresh market data via market data service."""
        if self._market_data is None:
            return WorkspaceOperationResult(
                False,
                WorkspaceType.MARKET,
                "Market data engine not configured",
            )
        status = self._market_data.market_status()
        self._cache.put_data(
            f"{session_id}:market",
            {
                "status": status.status.value,
                "exchange": status.exchange,
                "tick_count": self._market_data.tick_count(),
            },
        )
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            f"Market status: {status.status.value}",
        )

    def subscribe_symbol(
        self,
        session_id: str,
        symbol: str,
        exchange: str = "NSE",
        *,
        product_type: str = "CASH",
    ) -> WorkspaceOperationResult:
        """Queue symbol for subscription (activates when broker connects)."""
        if self._market_data is None:
            return WorkspaceOperationResult(False, WorkspaceType.MARKET, "No market data")
        self._market_data.subscribe(
            symbol,
            exchange,
            product_type=ProductType(product_type),
        )
        pending = self._market_data.connection_status().value != "Connected"
        message = f"Queued {symbol}" if pending else f"Subscribed to {symbol}"
        return WorkspaceOperationResult(
            True, WorkspaceType.MARKET, message, {"symbol": symbol}
        )

    def latest_quote(
        self,
        session_id: str,
        symbol: str,
        exchange: str = "NSE",
    ) -> WorkspaceOperationResult:
        """Return latest tick for symbol."""
        if self._market_data is None:
            return WorkspaceOperationResult(False, WorkspaceType.MARKET, "No market data")
        tick = self._market_data.latest_tick(symbol, exchange)
        payload = tick.model_dump(mode="json") if tick is not None else {}
        return WorkspaceOperationResult(
            tick is not None,
            WorkspaceType.MARKET,
            f"Latest {symbol}",
            payload,
        )

    def market_status(self, session_id: str) -> WorkspaceOperationResult:
        """Return live market status."""
        if self._market_data is None:
            return WorkspaceOperationResult(False, WorkspaceType.MARKET, "No market data")
        snap = self._market_data.market_status()
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            snap.status.value,
            {
                "status": snap.status.value,
                "exchange": snap.exchange,
                "connection": self._market_data.connection_status().value,
                "last_tick": str(self._market_data.last_tick_time() or ""),
            },
        )

    def watchlist(self, session_id: str, symbols: tuple[str, ...]) -> WorkspaceOperationResult:
        """Set watchlist symbols in memory (subscriptions remain pending)."""
        self._watchlists[session_id] = symbols
        self._cache.put_data(f"{session_id}:watchlist", symbols)
        if self._market_data is not None:
            self._market_data.load_watchlist(symbols)
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            f"Watchlist loaded ({len(symbols)} symbols, subscriptions pending)",
            symbols,
        )

    def market_overview(self, session_id: str) -> WorkspaceOperationResult:
        """Return market overview from live service."""
        cached = self._cache.get_data(f"{session_id}:market")
        status = self.market_status(session_id)
        payload = status.data or {}
        if cached:
            payload = {**cached, **payload}
        return WorkspaceOperationResult(
            True,
            WorkspaceType.MARKET,
            "Market overview",
            payload,
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

    def _resolve_market_data(self) -> MarketDataService | None:
        provider = self._engines.market_data
        return provider.service if provider is not None else None
