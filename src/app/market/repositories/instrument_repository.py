"""In-memory instrument repository with file and SQLite support."""

import json
import sqlite3
from pathlib import Path

from app.logging.logging_manager import get_logger
from app.market.exchanges.models import DEFAULT_UNDERLYINGS, UnderlyingMaster
from app.market.instrument_master.factory import InstrumentFactory
from app.market.instrument_master.models import Instrument
from app.market.repositories.data_loader import MarketDataLoader

logger = get_logger(__name__)


class InstrumentRepository:
    """Instrument repository backed by memory with YAML/JSON/SQLite loading."""

    def __init__(
        self, data_directory: Path, seed_directory: Path | None = None
    ) -> None:
        """Initialize repository paths."""
        self._data_directory = data_directory
        self._seed_directory = seed_directory
        self._instruments: dict[str, Instrument] = {}
        self._db_path = data_directory / "config.db"

    def initialize(self) -> None:
        """Load instruments from seed files and optional SQLite cache."""
        self._instruments.clear()
        self._load_defaults()
        self._load_seed_files()
        self._load_sqlite()
        logger.info(
            "Instrument repository loaded {count} instruments",
            count=len(self._instruments),
        )

    def close(self) -> None:
        """Persist instruments to SQLite and clear memory."""
        self._save_sqlite()
        self._instruments.clear()

    def get_all(self) -> list[Instrument]:
        """Return all instruments."""
        return list(self._instruments.values())

    def get_by_id(self, instrument_id: str) -> Instrument | None:
        """Return instrument by id."""
        return self._instruments.get(instrument_id)

    def get_by_symbol(self, trading_symbol: str) -> list[Instrument]:
        """Return instruments by trading symbol."""
        symbol = trading_symbol.upper()
        return [
            item
            for item in self._instruments.values()
            if item.trading_symbol.upper() == symbol
        ]

    def get_by_exchange(self, exchange: str) -> list[Instrument]:
        """Return instruments by exchange."""
        code = exchange.upper()
        return [
            item for item in self._instruments.values() if item.exchange.value == code
        ]

    def get_by_underlying(self, underlying: str) -> list[Instrument]:
        """Return instruments by underlying."""
        symbol = underlying.upper()
        return [
            item
            for item in self._instruments.values()
            if item.underlying.upper() == symbol
        ]

    def get_by_instrument_type(self, instrument_type: str) -> list[Instrument]:
        """Return instruments by type."""
        inst_type = instrument_type.upper()
        return [
            item
            for item in self._instruments.values()
            if item.instrument_type.value == inst_type
        ]

    def save(self, instrument: Instrument) -> None:
        """Save a single instrument."""
        self._instruments[instrument.instrument_id] = instrument

    def save_all(self, instruments: list[Instrument]) -> None:
        """Save multiple instruments."""
        for instrument in instruments:
            self.save(instrument)

    def _load_defaults(self) -> None:
        """Load built-in underlying master records."""
        for underlying in DEFAULT_UNDERLYINGS:
            instrument = InstrumentFactory.from_underlying(underlying)
            self.save(instrument)

    def _load_seed_files(self) -> None:
        """Load optional YAML/JSON seed files."""
        if self._seed_directory is None or not self._seed_directory.exists():
            return
        loader = MarketDataLoader()
        for path in sorted(self._seed_directory.glob("underlyings.*")):
            for record in loader.load_records(path):
                underlying = UnderlyingMaster.model_validate(record)
                self.save(InstrumentFactory.from_underlying(underlying))

    def _load_sqlite(self) -> None:
        """Load instruments from SQLite if present."""
        if not self._db_path.exists():
            return
        query = "SELECT payload FROM market_instruments"
        try:
            with sqlite3.connect(self._db_path) as connection:
                rows = connection.execute(query).fetchall()
        except sqlite3.Error:
            return
        for (payload,) in rows:
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                logger.warning("Skipping invalid instrument payload in SQLite")
                continue
            self.save(Instrument.model_validate(data))

    def _save_sqlite(self) -> None:
        """Persist instruments to SQLite."""
        self._data_directory.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS market_instruments "
                "(instrument_id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )
            connection.executemany(
                "INSERT OR REPLACE INTO market_instruments (instrument_id, payload) VALUES (?, ?)",
                [
                    (item.instrument_id, item.model_dump_json())
                    for item in self._instruments.values()
                ],
            )
            connection.commit()
