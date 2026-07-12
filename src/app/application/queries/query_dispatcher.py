"""Query dispatcher."""

from app.application.exceptions import InvalidApplicationInput
from app.application.models.enums import QueryType
from app.application.models.queries import ApplicationQuery, QueryResult
from app.application.services.ai_workspace_service import AIWorkspaceService
from app.application.services.market_workspace_service import MarketWorkspaceService
from app.application.services.portfolio_workspace_service import PortfolioWorkspaceService
from app.application.services.strategy_workspace_service import StrategyWorkspaceService
from app.application.session.session_manager import SessionManager
from app.application.validation.application_validator import ApplicationValidator


class QueryDispatcher:
    """Dispatch application queries to workspace services."""

    def __init__(
        self,
        validator: ApplicationValidator,
        sessions: SessionManager,
        portfolio: PortfolioWorkspaceService,
        strategy: StrategyWorkspaceService,
        market: MarketWorkspaceService,
        ai: AIWorkspaceService,
    ) -> None:
        """Initialize dispatcher."""
        self._validator = validator
        self._sessions = sessions
        self._portfolio = portfolio
        self._strategy = strategy
        self._market = market
        self._ai = ai

    def dispatch(self, query: ApplicationQuery) -> QueryResult:
        """Dispatch query and return result."""
        self._validator.validate_query(query)
        handlers = {
            QueryType.GET_PORTFOLIO: self._get_portfolio,
            QueryType.GET_MARKET: self._get_market,
            QueryType.GET_STRATEGY: self._get_strategy,
            QueryType.GET_REPORTS: self._get_reports,
            QueryType.GET_RECOMMENDATIONS: self._get_recommendations,
            QueryType.GET_WORKSPACE_STATE: self._get_workspace_state,
            QueryType.GET_SESSION: self._get_session,
        }
        handler = handlers.get(query.query_type)
        if handler is None:
            return QueryResult(query.query_type, False, error="unsupported query")
        return handler(query)

    def _get_portfolio(self, query: ApplicationQuery) -> QueryResult:
        portfolio_id = query.parameters.get("portfolio_id", "")
        summary = self._portfolio.summary(portfolio_id) if portfolio_id else None
        return QueryResult(query.query_type, True, summary)

    def _get_market(self, query: ApplicationQuery) -> QueryResult:
        result = self._market.market_overview(query.session_id)
        return QueryResult(query.query_type, result.success, result.data)

    def _get_strategy(self, query: ApplicationQuery) -> QueryResult:
        strategy_id = query.parameters.get("strategy_id", "")
        if strategy_id:
            strategy = self._strategy.get_strategy(strategy_id)
        else:
            result = self._strategy.list_strategies(query.session_id)
            strategy = result.data
        return QueryResult(query.query_type, True, strategy)

    def _get_reports(self, query: ApplicationQuery) -> QueryResult:
        key = query.parameters.get("report_key", f"{query.session_id}:portfolio-report")
        report = self._portfolio.get_cached_report(key)
        return QueryResult(query.query_type, report is not None, report)

    def _get_recommendations(self, query: ApplicationQuery) -> QueryResult:
        result = self._ai.recommendation_history(query.session_id)
        return QueryResult(query.query_type, result.success, result.data)

    def _get_workspace_state(self, query: ApplicationQuery) -> QueryResult:
        session = self._sessions.get(query.session_id)
        return QueryResult(query.query_type, True, session.workspaces)

    def _get_session(self, query: ApplicationQuery) -> QueryResult:
        session = self._sessions.get(query.session_id)
        return QueryResult(query.query_type, True, session)
