"""SQLite-backed named backtest result repository.

Distinct from BacktestCache, which is an in-memory, TTL-expiring cache of
the *latest* run per cache key (ephemeral by design). This repository is
for explicitly-named results the user chooses to keep (e.g. "Save Backtest
As..."), which must survive an app restart.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.backtesting.models.result import BacktestResult
from app.logging.logging_manager import get_logger
from app.persistence.dataclass_codec import from_json, to_json

logger = get_logger(__name__)


class BacktestResultRepository:
    """Persist named backtest results to backtest.db."""

    def __init__(self, database_path: Path) -> None:
        """Initialize repository path."""
        self._database_path = database_path

    def initialize(self) -> None:
        """Create table if needed."""
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS backtest_results "
                "(name TEXT PRIMARY KEY, payload TEXT NOT NULL, saved_at TEXT NOT NULL)"
            )
            connection.commit()
        logger.info("Backtest result repository initialized at {path}", path=self._database_path)

    def close(self) -> None:
        """Close repository (no persistent connection)."""
        return None

    def save(self, name: str, result: BacktestResult) -> None:
        """Save a named backtest result."""
        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                "INSERT OR REPLACE INTO backtest_results (name, payload, saved_at) VALUES (?, ?, ?)",
                (name, to_json(result), datetime.now(timezone.utc).isoformat()),
            )
            connection.commit()

    def get(self, name: str) -> BacktestResult | None:
        """Return a saved result by name."""
        with sqlite3.connect(self._database_path) as connection:
            row = connection.execute(
                "SELECT payload FROM backtest_results WHERE name = ?", (name,)
            ).fetchone()
        if row is None:
            return None
        return from_json(BacktestResult, row[0])

    def list_names(self) -> tuple[str, ...]:
        """Return all saved result names."""
        with sqlite3.connect(self._database_path) as connection:
            rows = connection.execute("SELECT name FROM backtest_results").fetchall()
        return tuple(row[0] for row in rows)

    def delete(self, name: str) -> bool:
        """Delete a saved result by name. Returns True if a row was removed."""
        with sqlite3.connect(self._database_path) as connection:
            cursor = connection.execute("DELETE FROM backtest_results WHERE name = ?", (name,))
            connection.commit()
        return cursor.rowcount > 0
