"""SQLite-backed strategy repository."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.logging.logging_manager import get_logger
from app.persistence.dataclass_codec import from_json, to_json
from app.strategy.models.strategy import Strategy

logger = get_logger(__name__)


class SqliteStrategyRepository:
    """Persist strategies to strategy.db."""

    def __init__(self, database_path: Path) -> None:
        """Initialize repository path."""
        self._database_path = database_path

    def initialize(self) -> None:
        """Create table if needed."""
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS strategies "
                "(strategy_id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL)"
            )
            connection.commit()
        logger.info("Strategy repository initialized at {path}", path=self._database_path)

    def close(self) -> None:
        """Close repository (no persistent connection)."""
        return None

    def save(self, strategy: Strategy) -> None:
        """Save or update strategy."""
        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                "INSERT OR REPLACE INTO strategies (strategy_id, payload, updated_at) VALUES (?, ?, ?)",
                (strategy.strategy_id, to_json(strategy), datetime.now(timezone.utc).isoformat()),
            )
            connection.commit()

    def get(self, strategy_id: str) -> Strategy | None:
        """Return strategy by id."""
        with sqlite3.connect(self._database_path) as connection:
            row = connection.execute(
                "SELECT payload FROM strategies WHERE strategy_id = ?", (strategy_id,)
            ).fetchone()
        if row is None:
            return None
        return from_json(Strategy, row[0])

    def delete(self, strategy_id: str) -> bool:
        """Delete strategy by id. Returns True if a row was removed."""
        with sqlite3.connect(self._database_path) as connection:
            cursor = connection.execute("DELETE FROM strategies WHERE strategy_id = ?", (strategy_id,))
            connection.commit()
        return cursor.rowcount > 0

    def list_all(self) -> tuple[Strategy, ...]:
        """Return all stored strategies."""
        with sqlite3.connect(self._database_path) as connection:
            rows = connection.execute("SELECT payload FROM strategies").fetchall()
        return tuple(from_json(Strategy, payload) for (payload,) in rows)
