"""Portfolio engine bootstrap."""

from pathlib import Path

from app.events.event_bus import EventBus
from app.portfolio.cache.portfolio_cache import PortfolioCache
from app.portfolio.engine.portfolio_engine import PortfolioEngine
from app.portfolio.repositories.memory_repository import InMemoryPortfolioRepository
from app.portfolio.repositories.sqlite_repository import SqlitePortfolioRepository
from app.portfolio.services.cash_service import CashService
from app.portfolio.services.holding_service import HoldingService
from app.portfolio.services.performance_service import PerformanceService
from app.portfolio.services.portfolio_service import PortfolioService
from app.portfolio.services.position_service import PositionService
from app.portfolio.services.transaction_service import TransactionService
from app.portfolio.validation.portfolio_validator import PortfolioValidator


class PortfolioProvider:
    """Wire portfolio engine dependencies."""

    def __init__(self, event_bus: EventBus | None = None, data_directory: Path | None = None) -> None:
        """Initialize provider.

        Portfolios persist to portfolio.db when `data_directory` is given;
        otherwise falls back to the original in-memory-only repository.
        """
        self.engine = PortfolioEngine()
        self.validator = PortfolioValidator()
        self.cache = PortfolioCache()
        if data_directory is not None:
            self.repository = SqlitePortfolioRepository(data_directory / "portfolio.db")
            self.repository.initialize()
        else:
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
