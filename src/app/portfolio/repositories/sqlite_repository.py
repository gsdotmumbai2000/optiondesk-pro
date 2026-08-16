"""SQLite-backed portfolio repository."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.logging.logging_manager import get_logger
from app.persistence.dataclass_codec import from_json, to_json
from app.portfolio.models.portfolio import Portfolio

logger = get_logger(__name__)


class SqlitePortfolioRepository:
    """Persist portfolios to portfolio.db."""

    def __init__(self, database_path: Path) -> None:
        """Initialize repository path."""
        self._database_path = database_path

    def initialize(self) -> None:
        """Create table if needed."""
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS portfolios "
                "(portfolio_id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL)"
            )
            connection.commit()
        logger.info("Portfolio repository initialized at {path}", path=self._database_path)

    def close(self) -> None:
        """Close repository (no persistent connection)."""
        return None

    def save(self, portfolio: Portfolio) -> None:
        """Persist portfolio."""
        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                "INSERT OR REPLACE INTO portfolios (portfolio_id, payload, updated_at) VALUES (?, ?, ?)",
                (portfolio.portfolio_id, to_json(portfolio), datetime.now(timezone.utc).isoformat()),
            )
            connection.commit()

    def get(self, portfolio_id: str) -> Portfolio | None:
        """Return portfolio by id."""
        with sqlite3.connect(self._database_path) as connection:
            row = connection.execute(
                "SELECT payload FROM portfolios WHERE portfolio_id = ?", (portfolio_id,)
            ).fetchone()
        if row is None:
            return None
        return from_json(Portfolio, row[0])

    def delete(self, portfolio_id: str) -> None:
        """Remove portfolio."""
        with sqlite3.connect(self._database_path) as connection:
            connection.execute("DELETE FROM portfolios WHERE portfolio_id = ?", (portfolio_id,))
            connection.commit()

    def list_ids(self) -> tuple[str, ...]:
        """Return all portfolio ids."""
        with sqlite3.connect(self._database_path) as connection:
            rows = connection.execute("SELECT portfolio_id FROM portfolios").fetchall()
        return tuple(row[0] for row in rows)

    def count(self) -> int:
        """Return portfolio count."""
        with sqlite3.connect(self._database_path) as connection:
            row = connection.execute("SELECT COUNT(*) FROM portfolios").fetchone()
        return row[0]
