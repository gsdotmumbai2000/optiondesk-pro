"""SQLite market data repository."""

import json
import sqlite3
import threading
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.logging.logging_manager import get_logger
from app.market_data.models import HistoricalBar, MarketStatistics

logger = get_logger(__name__)


class MarketDataRepository:
    """Persist market data to market.db.

    Holds one long-lived connection in WAL mode rather than opening a fresh
    connection (and fsync-ing a rollback journal) on every call -- live
    quote/tick volume calls `save_statistics` tens of times per second, and
    reconnect-plus-fsync-per-write at that rate was measured consuming ~33%
    of total app CPU under a live, actively-ticking option chain.
    """

    def __init__(self, database_path: Path) -> None:
        """Initialize repository path."""
        self._database_path = database_path
        self._connection: sqlite3.Connection | None = None
        self._lock = threading.Lock()

    def initialize(self) -> None:
        """Open the persistent connection and create tables if needed."""
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._database_path, check_same_thread=False)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        with self._lock:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS historical_bars "
                "(id INTEGER PRIMARY KEY, symbol TEXT, exchange TEXT, payload TEXT)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS market_statistics "
                "(symbol TEXT, exchange TEXT, payload TEXT, PRIMARY KEY(symbol, exchange))"
            )
            connection.commit()
        self._connection = connection
        logger.info("Market data repository initialized at {path}", path=self._database_path)

    def close(self) -> None:
        """Close the persistent connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def save_bars(self, bars: list[HistoricalBar]) -> None:
        """Persist historical bars."""
        if not bars or self._connection is None:
            return
        with self._lock:
            self._connection.executemany(
                "INSERT INTO historical_bars (symbol, exchange, payload) VALUES (?, ?, ?)",
                [
                    (bar.symbol, bar.exchange, bar.model_dump_json())
                    for bar in bars
                ],
            )
            self._connection.commit()

    def load_bars(self, symbol: str, exchange: str, limit: int = 500) -> list[HistoricalBar]:
        """Load historical bars."""
        if self._connection is None:
            return []
        query = (
            "SELECT payload FROM historical_bars WHERE symbol = ? AND exchange = ? "
            "ORDER BY id DESC LIMIT ?"
        )
        with self._lock:
            rows = self._connection.execute(query, (symbol, exchange, limit)).fetchall()
        bars: list[HistoricalBar] = []
        for (payload,) in rows:
            bars.append(HistoricalBar.model_validate(json.loads(payload)))
        return list(reversed(bars))

    def save_statistics(self, stats: MarketStatistics) -> None:
        """Persist market statistics."""
        if self._connection is None:
            return
        with self._lock:
            self._connection.execute(
                "INSERT OR REPLACE INTO market_statistics (symbol, exchange, payload) "
                "VALUES (?, ?, ?)",
                (stats.symbol, stats.exchange, stats.model_dump_json()),
            )
            self._connection.commit()

    def load_statistics(self, symbol: str, exchange: str) -> MarketStatistics | None:
        """Load market statistics."""
        if self._connection is None:
            return None
        with self._lock:
            row = self._connection.execute(
                "SELECT payload FROM market_statistics WHERE symbol = ? AND exchange = ?",
                (symbol, exchange),
            ).fetchone()
        if row is None:
            return None
        return MarketStatistics.model_validate(json.loads(row[0]))
