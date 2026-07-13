"""Portfolio workspace service."""

from datetime import datetime, timezone
from decimal import Decimal

from app.application.cache.workspace_cache import WorkspaceCache
from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult, WorkspaceView
from app.application.ports.live_analytics_port import LiveAnalyticsPort
from app.application.ports.market_data_port import MarketDataPort
from app.application.registry.engine_registry import EngineRegistry
from app.application.services.live_analytics_support import LiveAnalyticsSupport
from app.application.services.market_data_support import MarketDataSupport
from app.application.session.session_manager import SessionManager
from app.monitor.models.request import MonitorAnalysisRequest
from app.monitor.models.result import MonitorResult
from app.portfolio.models.portfolio import Portfolio, PortfolioSummary
from app.portfolio.models.request import PortfolioAnalysisRequest
from app.portfolio.models.result import PortfolioResult


class PortfolioWorkspaceService(MarketDataSupport, LiveAnalyticsSupport):
    """Portfolio management workspace API for UI."""

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

    def load_portfolio(
        self,
        session_id: str,
        portfolio_id: str,
    ) -> WorkspaceOperationResult:
        """Load portfolio by id."""
        portfolio = self._engines.portfolio.repository.get(portfolio_id)
        if portfolio is None:
            return WorkspaceOperationResult(
                False,
                WorkspaceType.PORTFOLIO,
                f"Portfolio not found: {portfolio_id}",
            )
        self._cache.put_data(portfolio_id, portfolio)
        self._sessions.set_active_workspace(session_id, WorkspaceType.PORTFOLIO, portfolio_id)
        return WorkspaceOperationResult(
            True,
            WorkspaceType.PORTFOLIO,
            "Portfolio loaded",
            portfolio,
        )

    def create_portfolio(
        self,
        session_id: str,
        name: str,
        initial_cash: Decimal,
    ) -> Portfolio:
        """Create new portfolio."""
        portfolio = self._engines.portfolio.service.create_portfolio(name, initial_cash)
        self._cache.put_data(portfolio.portfolio_id, portfolio)
        self._sessions.set_active_workspace(
            session_id,
            WorkspaceType.PORTFOLIO,
            portfolio.portfolio_id,
        )
        return portfolio

    def refresh_portfolio(
        self,
        session_id: str,
        request: PortfolioAnalysisRequest,
    ) -> PortfolioResult:
        """Refresh portfolio analytics."""
        result = self._engines.portfolio.service.calculate(request)
        self._cache.put_data(f"{session_id}:portfolio", result)
        return result

    def monitor_portfolio(
        self,
        session_id: str,
        request: MonitorAnalysisRequest,
    ) -> MonitorResult:
        """Monitor portfolio via monitor engine."""
        result = self._engines.monitor.service.evaluate(request)
        self._cache.put_data(f"{session_id}:monitor", result)
        return result

    def generate_report(
        self,
        session_id: str,
        portfolio_result: PortfolioResult,
    ) -> WorkspaceOperationResult:
        """Generate portfolio report."""
        report = self._engines.portfolio.service.build_report(portfolio_result)
        key = f"{session_id}:portfolio-report"
        self._cache.put_report(key, report)
        return WorkspaceOperationResult(
            True,
            WorkspaceType.PORTFOLIO,
            "Report generated",
            report,
        )

    def export_report(self, session_id: str, report_key: str) -> WorkspaceOperationResult:
        """Export cached report (framework)."""
        report = self._cache.get_report(report_key)
        if report is None:
            return WorkspaceOperationResult(
                False,
                WorkspaceType.PORTFOLIO,
                "Report not found",
            )
        return WorkspaceOperationResult(
            True,
            WorkspaceType.PORTFOLIO,
            "Report ready for export",
            report,
        )

    def summary(self, portfolio_id: str) -> PortfolioSummary | None:
        """Return portfolio summary."""
        return self._engines.portfolio.service.summary(portfolio_id)

    def get_cached_report(self, report_key: str):
        """Return cached report by key."""
        return self._cache.get_report(report_key)

    def view(self, session_id: str) -> WorkspaceView:
        """Return portfolio workspace view."""
        session = self._sessions.get(session_id)
        entity = next(
            (w.entity_id for w in session.workspaces if w.workspace == WorkspaceType.PORTFOLIO),
            "",
        )
        return WorkspaceView(
            workspace=WorkspaceType.PORTFOLIO,
            title="Portfolio Workspace",
            summary=f"Portfolio: {entity or 'none'}",
            entity_id=entity,
            updated_at=datetime.now(timezone.utc),
        )

    def position_market_price(
        self,
        session_id: str,
        symbol: str,
        exchange: str = "NSE",
    ) -> WorkspaceOperationResult:
        """Return live price for a portfolio position."""
        tick = self.latest_tick(symbol, exchange)
        payload = tick.model_dump(mode="json") if tick is not None else {}
        return WorkspaceOperationResult(
            tick is not None,
            WorkspaceType.PORTFOLIO,
            f"Market price for {symbol}",
            payload,
        )

    def monitor_live_prices(
        self,
        session_id: str,
        symbols: tuple[str, ...],
        exchange: str = "NSE",
    ) -> WorkspaceOperationResult:
        """Return live prices for position monitor symbols."""
        prices = {
            symbol: str(self.latest_price(symbol, exchange) or "")
            for symbol in symbols
        }
        self._cache.put_data(f"{session_id}:monitor:prices", prices)
        return WorkspaceOperationResult(
            True,
            WorkspaceType.PORTFOLIO,
            f"Live prices for {len(symbols)} symbols",
            prices,
        )

    def live_position_analytics(
        self,
        session_id: str,
        symbol: str,
        exchange: str = "NSE",
        expiry_date: str = "",
    ) -> WorkspaceOperationResult:
        """Return live analytics for a monitored position."""
        snapshot = self.live_analytics_snapshot(symbol, exchange, expiry_date)
        payload = {}
        if snapshot is not None and snapshot.position_greeks is not None:
            payload = dict(snapshot.position_greeks)
        return WorkspaceOperationResult(
            snapshot is not None,
            WorkspaceType.PORTFOLIO,
            f"Live analytics for {symbol}",
            payload,
        )
