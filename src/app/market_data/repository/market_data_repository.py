"""SQLite market data repository."""

import json
import sqlite3
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.logging.logging_manager import get_logger
from app.market_data.models import HistoricalBar, MarketStatistics

logger = get_logger(__name__)


class MarketDataRepository:
    """Persist market data to market.db."""

    def __init__(self, database_path: Path) -> None:
        """Initialize repository path."""
        self._database_path = database_path

    def initialize(self) -> None:
        """Create tables if needed."""
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS historical_bars "
                "(id INTEGER PRIMARY KEY, symbol TEXT, exchange TEXT, payload TEXT)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS market_statistics "
                "(symbol TEXT, exchange TEXT, payload TEXT, PRIMARY KEY(symbol, exchange))"
            )
            connection.commit()
        logger.info("Market data repository initialized at {path}", path=self._database_path)

    def close(self) -> None:
        """Close repository (no persistent connection)."""
        return None

    def save_bars(self, bars: list[HistoricalBar]) -> None:
        """Persist historical bars."""
        if not bars:
            return
        with sqlite3.connect(self._database_path) as connection:
            connection.executemany(
                "INSERT INTO historical_bars (symbol, exchange, payload) VALUES (?, ?, ?)",
                [
                    (bar.symbol, bar.exchange, bar.model_dump_json())
                    for bar in bars
                ],
            )
            connection.commit()

    def load_bars(self, symbol: str, exchange: str, limit: int = 500) -> list[HistoricalBar]:
        """Load historical bars."""
        query = (
            "SELECT payload FROM historical_bars WHERE symbol = ? AND exchange = ? "
            "ORDER BY id DESC LIMIT ?"
        )
        with sqlite3.connect(self._database_path) as connection:
            rows = connection.execute(query, (symbol, exchange, limit)).fetchall()
        bars: list[HistoricalBar] = []
        for (payload,) in rows:
            bars.append(HistoricalBar.model_validate(json.loads(payload)))
        return list(reversed(bars))

    def save_statistics(self, stats: MarketStatistics) -> None:
        """Persist market statistics."""
        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                "INSERT OR REPLACE INTO market_statistics (symbol, exchange, payload) "
                "VALUES (?, ?, ?)",
                (stats.symbol, stats.exchange, stats.model_dump_json()),
            )
            connection.commit()

    def load_statistics(self, symbol: str, exchange: str) -> MarketStatistics | None:
        """Load market statistics."""
        with sqlite3.connect(self._database_path) as connection:
            row = connection.execute(
                "SELECT payload FROM market_statistics WHERE symbol = ? AND exchange = ?",
                (symbol, exchange),
            ).fetchone()
        if row is None:
            return None
        return MarketStatistics.model_validate(json.loads(row[0]))
