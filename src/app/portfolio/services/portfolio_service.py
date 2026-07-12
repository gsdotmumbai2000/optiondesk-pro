"""Portfolio application service."""

from datetime import datetime, timezone
from decimal import Decimal

from app.events.event_bus import EventBus
from app.portfolio.cache.portfolio_cache import PortfolioCache
from app.portfolio.engine.portfolio_engine import PortfolioEngine
from app.portfolio.events import (
    PerformanceUpdatedEvent,
    PortfolioCreatedEvent,
    PortfolioUpdatedEvent,
    PositionClosedEvent,
    PositionOpenedEvent,
    TradeRecordedEvent,
)
from app.portfolio.exceptions import PortfolioException
from app.portfolio.models.cash import CashAccount
from app.portfolio.models.enums import PortfolioModelVersion
from app.portfolio.models.portfolio import Portfolio, PortfolioSnapshot, PortfolioSummary
from app.portfolio.models.request import PortfolioAnalysisRequest
from app.portfolio.models.result import PortfolioResult
from app.portfolio.providers.cache_keys import build_cache_key
from app.portfolio.repositories.memory_repository import InMemoryPortfolioRepository
from app.portfolio.reports.report_builder import ReportBuilder
from app.portfolio.validation.portfolio_validator import PortfolioValidator
from app.utils.uuid_helper import generate_uuid


class PortfolioService:
    """Orchestrate portfolio analytics, caching, and events."""

    def __init__(
        self,
        engine: PortfolioEngine,
        validator: PortfolioValidator | None = None,
        cache: PortfolioCache | None = None,
        repository: InMemoryPortfolioRepository | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize service."""
        self._engine = engine
        self._validator = validator or PortfolioValidator()
        self._cache = cache or PortfolioCache()
        self._repository = repository or InMemoryPortfolioRepository()
        self._event_bus = event_bus
        self._report_builder = ReportBuilder()

    @property
    def cache(self) -> PortfolioCache:
        """Return portfolio cache."""
        return self._cache

    @property
    def repository(self) -> InMemoryPortfolioRepository:
        """Return portfolio repository."""
        return self._repository

    def create_portfolio(
        self,
        name: str,
        initial_cash: Decimal,
        currency: str = "INR",
    ) -> Portfolio:
        """Create and persist a new portfolio."""
        portfolio = Portfolio(
            portfolio_id=generate_uuid(),
            name=name,
            cash_account=CashAccount(
                balance=initial_cash,
                available=initial_cash,
                reserved=Decimal("0"),
                currency=currency,
            ),
            holdings=(),
            open_positions=(),
            closed_positions=(),
            pending_orders=(),
            executed_orders=(),
            transactions=(),
            version=PortfolioModelVersion.V1,
        )
        self._validator.validate_portfolio(portfolio)
        self._repository.save(portfolio)
        self._publish_created(portfolio.portfolio_id)
        return portfolio

    def calculate(
        self,
        request: PortfolioAnalysisRequest,
        initial_capital: Decimal = Decimal("0"),
    ) -> PortfolioResult:
        """Calculate and cache portfolio analytics."""
        try:
            self._validator.validate_request(request)
            portfolio = self._repository.get(request.portfolio_id)
            if portfolio is None:
                raise PortfolioException(
                    f"portfolio not found: {request.portfolio_id}"
                )
            self._validator.validate_portfolio(portfolio)
            key = build_cache_key(request)
            history = self._cache.get_value_history(key)
            updated, result = self._engine.calculate(
                request,
                portfolio,
                history,
                initial_capital,
            )
            self._repository.save(updated)
            snapshot = PortfolioSnapshot(
                portfolio_id=updated.portfolio_id,
                captured_at=datetime.now(timezone.utc),
                portfolio_value=result.portfolio_value,
                cash_balance=result.cash_balance,
                realized_pnl=result.realized_pnl,
                unrealized_pnl=result.unrealized_pnl,
            )
            self._cache.put(key, result, snapshot)
            self._publish_events(key, result, request)
            return result
        except PortfolioException:
            raise

    def get_latest(self, request: PortfolioAnalysisRequest) -> PortfolioResult | None:
        """Return latest cached result."""
        return self._cache.get_latest(build_cache_key(request))

    def refresh(
        self,
        request: PortfolioAnalysisRequest,
        initial_capital: Decimal = Decimal("0"),
    ) -> PortfolioResult:
        """Invalidate and recalculate."""
        self._cache.invalidate(build_cache_key(request))
        return self.calculate(request, initial_capital)

    def summary(self, portfolio_id: str) -> PortfolioSummary | None:
        """Return portfolio summary."""
        portfolio = self._repository.get(portfolio_id)
        if portfolio is None:
            return None
        value = sum(h.market_value for h in portfolio.holdings)
        return PortfolioSummary(
            portfolio_id=portfolio_id,
            portfolio_value=value,
            cash_balance=portfolio.cash_account.balance,
            holdings_count=len(portfolio.holdings),
            open_positions_count=len(portfolio.open_positions),
        )

    def build_report(self, result: PortfolioResult):
        """Build portfolio report."""
        return self._report_builder.build_portfolio_report(result)

    def _publish_created(self, portfolio_id: str) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            PortfolioCreatedEvent(payload={"portfolio_id": portfolio_id})
        )

    def _publish_events(
        self,
        key: str,
        result: PortfolioResult,
        request: PortfolioAnalysisRequest,
    ) -> None:
        if self._event_bus is None:
            return
        payload = {"key": key, "portfolio_value": str(result.portfolio_value)}
        self._event_bus.publish(PortfolioUpdatedEvent(payload=payload))
        self._event_bus.publish(PerformanceUpdatedEvent(payload=payload))
        for trade in request.trade_executions:
            self._event_bus.publish(
                TradeRecordedEvent(payload={"trade_id": trade.trade_id})
            )
        if result.open_positions:
            self._event_bus.publish(PositionOpenedEvent(payload=payload))
        if result.closed_positions:
            self._event_bus.publish(PositionClosedEvent(payload=payload))
