"""Replay engine tests."""

import json
import time
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock

from app.market_data.models.tick import TickSnapshot
from app.simulator.player.replay_engine import ReplayEngine, find_latest_recording


def _write_recording(path: Path, symbols: list[str]) -> None:
    lines = [
        json.dumps(
            {
                "captured_at": "2026-08-21T04:00:00+00:00",
                "tick": {"symbol": symbol, "exchange": "NSE", "ltp": "22000"},
            }
        )
        for symbol in symbols
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_find_latest_recording(tmp_path: Path) -> None:
    """Should pick the lexicographically-last matching recording file."""
    (tmp_path / "nifty_20260819.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "nifty_20260821.jsonl").write_text("", encoding="utf-8")
    latest = find_latest_recording(tmp_path)
    assert latest is not None
    assert latest.name == "nifty_20260821.jsonl"


def test_find_latest_recording_missing_dir(tmp_path: Path) -> None:
    """Should return None when the recordings directory doesn't exist."""
    assert find_latest_recording(tmp_path / "missing") is None


def test_replay_enqueues_ticks_with_fresh_timestamp(tmp_path: Path) -> None:
    """Replay should push each recorded tick into the dispatcher with a fresh timestamp."""
    recording = tmp_path / "nifty_20260821.jsonl"
    _write_recording(recording, ["NIFTY", "NIFTY24DEC22000CE"])
    dispatcher = MagicMock()
    engine = ReplayEngine(dispatcher, recording, min_interval_seconds=0.01)

    engine.start()
    time.sleep(0.2)
    engine.stop()

    assert dispatcher.enqueue.call_count >= 2
    first_tick = dispatcher.enqueue.call_args_list[0].args[0]
    assert isinstance(first_tick, TickSnapshot)
    assert first_tick.symbol == "NIFTY"
    assert first_tick.ltp == Decimal("22000")
    assert first_tick.timestamp is not None


def test_replay_loops(tmp_path: Path) -> None:
    """Replay should loop back to the start after reaching end of file."""
    recording = tmp_path / "nifty_20260821.jsonl"
    _write_recording(recording, ["NIFTY"])
    dispatcher = MagicMock()
    engine = ReplayEngine(dispatcher, recording, min_interval_seconds=0.01)

    engine.start()
    time.sleep(0.2)
    engine.stop()

    assert dispatcher.enqueue.call_count > 1


def test_no_recording_does_not_start_thread(tmp_path: Path) -> None:
    """Missing recording file should not start a replay thread."""
    dispatcher = MagicMock()
    engine = ReplayEngine(dispatcher, tmp_path / "missing.jsonl")
    engine.start()
    time.sleep(0.05)
    engine.stop()
    dispatcher.enqueue.assert_not_called()
