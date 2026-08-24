"""Tick recorder tests."""

import json
from pathlib import Path

from app.events.event_bus import EventBus
from app.market_data.events import TickReceivedEvent
from app.simulator.events import RecordingTickCapturedEvent
from app.simulator.recorder.tick_recorder import TickRecorder


def _tick_event(symbol: str, ltp: str = "22000") -> TickReceivedEvent:
    return TickReceivedEvent(
        payload={"tick": {"symbol": symbol, "exchange": "NSE", "ltp": ltp}}
    )


def test_records_nifty_ticks_only(tmp_path: Path) -> None:
    """Recorder should persist NIFTY-prefixed ticks and skip other indices."""
    bus = EventBus()
    recorder = TickRecorder(bus, tmp_path)
    recorder.start()

    bus.publish(_tick_event("NIFTY"))
    bus.publish(_tick_event("BANKNIFTY"))
    bus.publish(_tick_event("FINNIFTY"))
    bus.publish(_tick_event("MIDCPNIFTY"))
    bus.publish(_tick_event("NIFTY24DEC22000CE"))

    assert recorder.tick_count == 2
    lines = recorder.output_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    symbols = [json.loads(line)["tick"]["symbol"] for line in lines]
    assert symbols == ["NIFTY", "NIFTY24DEC22000CE"]


def test_ignores_malformed_events(tmp_path: Path) -> None:
    """Recorder should ignore events without a tick-shaped payload."""
    bus = EventBus()
    recorder = TickRecorder(bus, tmp_path)
    recorder.start()

    bus.publish(TickReceivedEvent(payload={}))
    bus.publish(TickReceivedEvent(payload={"tick": "not-a-dict"}))

    assert recorder.tick_count == 0


def test_publishes_recording_tick_captured_event(tmp_path: Path) -> None:
    """Recorder should publish a UI-facing event per recorded tick, with a running count."""
    bus = EventBus()
    recorder = TickRecorder(bus, tmp_path)
    captured: list[dict] = []
    bus.subscribe(RecordingTickCapturedEvent, lambda event: captured.append(event.payload))
    recorder.start()

    bus.publish(_tick_event("NIFTY"))
    bus.publish(_tick_event("NIFTY"))
    bus.publish(_tick_event("BANKNIFTY"))  # filtered out, should not publish

    assert [c["tick_count"] for c in captured] == [1, 2]
