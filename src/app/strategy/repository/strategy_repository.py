"""In-memory strategy repository."""

from threading import RLock

from app.strategy.models.strategy import Strategy


class StrategyRepository:
    """In-memory strategy storage (no database)."""

    def __init__(self) -> None:
        """Initialize repository."""
        self._lock = RLock()
        self._strategies: dict[str, Strategy] = {}

    def save(self, strategy: Strategy) -> None:
        """Save or update strategy."""
        with self._lock:
            self._strategies[strategy.strategy_id] = strategy

    def get(self, strategy_id: str) -> Strategy | None:
        """Return strategy by id."""
        with self._lock:
            return self._strategies.get(strategy_id)

    def delete(self, strategy_id: str) -> bool:
        """Delete strategy by id."""
        with self._lock:
            return self._strategies.pop(strategy_id, None) is not None

    def list_all(self) -> tuple[Strategy, ...]:
        """Return all stored strategies."""
        with self._lock:
            return tuple(self._strategies.values())
