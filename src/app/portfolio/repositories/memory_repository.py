"""In-memory portfolio repository."""

from threading import RLock

from app.portfolio.models.portfolio import Portfolio


class InMemoryPortfolioRepository:
    """Thread-safe in-memory portfolio store."""

    def __init__(self) -> None:
        """Initialize repository."""
        self._lock = RLock()
        self._portfolios: dict[str, Portfolio] = {}

    def save(self, portfolio: Portfolio) -> None:
        """Persist portfolio."""
        with self._lock:
            self._portfolios[portfolio.portfolio_id] = portfolio

    def get(self, portfolio_id: str) -> Portfolio | None:
        """Return portfolio by id."""
        with self._lock:
            return self._portfolios.get(portfolio_id)

    def delete(self, portfolio_id: str) -> None:
        """Remove portfolio."""
        with self._lock:
            self._portfolios.pop(portfolio_id, None)

    def list_ids(self) -> tuple[str, ...]:
        """Return all portfolio ids."""
        with self._lock:
            return tuple(self._portfolios.keys())

    def count(self) -> int:
        """Return portfolio count."""
        with self._lock:
            return len(self._portfolios)
