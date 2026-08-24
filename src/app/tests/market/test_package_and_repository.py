"""Package exports and repository persistence tests."""

import json
import sqlite3
from pathlib import Path

import app.market as market_package
from app.market.bootstrap import MarketMasterProvider
from app.market.enums import ExchangeCode, InstrumentType
from app.market.instrument_master.models import (Instrument,
                                                 InstrumentSpecification)
from app.market.repositories.instrument_repository import InstrumentRepository


def test_lazy_package_exports() -> None:
    """Market package should expose lazy exports."""
    assert market_package.MarketMasterProvider is not None
    assert market_package.MarketCache is not None
    assert market_package.InstrumentService is not None


def test_sqlite_round_trip(tmp_path: Path) -> None:
    """Instruments should persist to and reload from SQLite."""
    repo = InstrumentRepository(tmp_path)
    repo.initialize()
    original_count = len(repo.get_all())
    repo.close()

    repo2 = InstrumentRepository(tmp_path)
    repo2.initialize()
    assert len(repo2.get_all()) == original_count
    repo2.close()


def test_repository_queries(tmp_path: Path) -> None:
    """Repository search methods should filter correctly."""
    repo = InstrumentRepository(tmp_path)
    repo.initialize()
    assert repo.get_by_id("NSEFO:NIFTY") is not None
    assert len(repo.get_by_symbol("NIFTY")) >= 1
    assert len(repo.get_by_exchange("NSEFO")) >= 1
    assert len(repo.get_by_underlying("NIFTY")) >= 1
    assert len(repo.get_by_instrument_type("INDEX")) >= 5
    repo.close()


def test_repository_loads_corrupt_sqlite(tmp_path: Path) -> None:
    """Corrupt SQLite data should be ignored gracefully."""
    db_path = tmp_path / "config.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "CREATE TABLE market_instruments (instrument_id TEXT PRIMARY KEY, payload TEXT)"
        )
        connection.execute(
            "INSERT INTO market_instruments VALUES (?, ?)",
            ("BAD:1", "not-json"),
        )
        connection.commit()
    repo = InstrumentRepository(tmp_path)
    repo.initialize()
    assert len(repo.get_all()) >= 5
    repo.close()


def test_repository_save_custom_instrument(tmp_path: Path) -> None:
    """Custom instruments should be saved to SQLite on close."""
    repo = InstrumentRepository(tmp_path)
    repo.initialize()
    instrument = Instrument(
        instrument_id="NSEFO:CUSTOM",
        trading_symbol="CUSTOM",
        display_name="Custom",
        underlying="CUSTOM",
        exchange=ExchangeCode.NSEFO,
        segment="FO",
        instrument_type=InstrumentType.STOCK,
        specification=InstrumentSpecification(
            tick_size=1,
            lot_size=1,
            freeze_quantity=1,
            strike_interval=1,
        ),
    )
    repo.save(instrument)
    repo.close()

    with sqlite3.connect(tmp_path / "config.db") as connection:
        row = connection.execute(
            "SELECT payload FROM market_instruments WHERE instrument_id = ?",
            ("NSEFO:CUSTOM",),
        ).fetchone()
    assert row is not None
    data = json.loads(row[0])
    assert data["trading_symbol"] == "CUSTOM"


def test_default_underlying_ignores_stale_sqlite_cache(tmp_path: Path) -> None:
    """A previous run's close() snapshots NIFTY's spec (lot_size=65 today)
    into SQLite. If a later code change revises DEFAULT_UNDERLYINGS (e.g.
    NSE's next lot-size revision), the next startup must use the new code
    value, not resurrect the stale cached one -- this is the exact bug that
    made a freshly-added leg still price off an old NIFTY lot size after
    DEFAULT_UNDERLYINGS had already been updated in code."""
    repo = InstrumentRepository(tmp_path)
    repo.initialize()
    repo.close()  # snapshots current NIFTY spec (lot_size=65) to SQLite

    with sqlite3.connect(tmp_path / "config.db") as connection:
        row = connection.execute(
            "SELECT payload FROM market_instruments WHERE instrument_id = ?",
            ("NSEFO:NIFTY",),
        ).fetchone()
    assert row is not None
    stale = json.loads(row[0])
    stale["specification"]["lot_size"] = 25  # simulate an old cached value
    with sqlite3.connect(tmp_path / "config.db") as connection:
        connection.execute(
            "UPDATE market_instruments SET payload = ? WHERE instrument_id = ?",
            (json.dumps(stale), "NSEFO:NIFTY"),
        )
        connection.commit()

    repo2 = InstrumentRepository(tmp_path)
    repo2.initialize()

    assert repo2.get_by_id("NSEFO:NIFTY").specification.lot_size == 65
    repo2.close()


def test_market_calendar_special_session(market_provider: MarketMasterProvider) -> None:
    """Market calendar should detect special sessions."""
    calendar = market_provider.cache.market_calendar
    assert calendar.get_config("NSE") is not None
    assert (
        calendar.is_special_session("NSE", __import__("datetime").date(2026, 1, 5))
        is False
    )
