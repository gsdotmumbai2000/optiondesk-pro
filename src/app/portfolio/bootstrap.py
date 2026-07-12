"""Portfolio engine bootstrap."""

from app.events.event_bus import EventBus
from app.portfolio.cache.portfolio_cache import PortfolioCache
from app.portfolio.engine.portfolio_engine import PortfolioEngine
from app.portfolio.repositories.memory_repository import InMemoryPortfolioRepository
from app.portfolio.services.cash_service import CashService
from app.portfolio.services.holding_service import HoldingService
from app.portfolio.services.performance_service import PerformanceService
from app.portfolio.services.portfolio_service import PortfolioService
from app.portfolio.services.position_service import PositionService
from app.portfolio.services.transaction_service import TransactionService
from app.portfolio.validation.portfolio_validator import PortfolioValidator


class PortfolioProvider:
    """Wire portfolio engine dependencies."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize provider."""
        self.engine = PortfolioEngine()
        self.validator = PortfolioValidator()
        self.cache = PortfolioCache()
        self.repository = InMemoryPortfolioRepository()
        self.position_service = PositionService()
        self.holding_service = HoldingService()
        self.cash_service = CashService()
        self.transaction_service = TransactionService()
        self.performance_service = PerformanceService()
        self.service = PortfolioService(
            self.engine,
            self.validator,
            self.cache,
            self.repository,
            event_bus,
        )
