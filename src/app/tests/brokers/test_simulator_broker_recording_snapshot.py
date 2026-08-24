"""Regression test: simulator broker must seed option chain/quote from the

recording, not return empty results. Caught via manual end-to-end testing:
NIFTY spot updated live but the option chain grid stayed blank, because the
grid's initial load goes through BrokerInterface.get_option_chain() before
any ticks have replayed, and the original stub always returned an empty
OptionChain.
"""

import json
from decimal import Decimal
from pathlib import Path

from app.brokers.shared.models import OptionChainRequest
from app.brokers.simulator.broker import SimulatorBroker
from app.config.models.app_config import BrokerConfig


def _write_recording(path: Path) -> None:
    ticks = [
        {"symbol": "NIFTY", "exchange": "NSE", "ltp": "24200", "product_type": ""},
        {
            "symbol": "NIFTY-25-Aug-2026-24200-CE",
            "exchange": "NFO",
            "ltp": "120.5",
            "open_interest": 1000,
            "volume": 500,
            "bid": "120",
            "ask": "121",
            "product_type": "Options",
            "expiry_date": "25-Aug-2026",
            "strike_price": "24200",
            "option_right": "Call",
        },
        {
            "symbol": "NIFTY-25-Aug-2026-24200-PE",
            "exchange": "NFO",
            "ltp": "95.25",
            "open_interest": 800,
            "volume": 300,
            "bid": "95",
            "ask": "96",
            "product_type": "Options",
            "expiry_date": "25-Aug-2026",
            "strike_price": "24200",
            "option_right": "Put",
        },
    ]
    lines = [json.dumps({"captured_at": "2026-08-21T08:00:00+00:00", "tick": t}) for t in ticks]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_get_option_chain_seeds_from_recording(tmp_path: Path) -> None:
    """SimulatorBroker should return real strikes/prices from the recording, not empty."""
    recordings_dir = tmp_path / "simulator" / "recordings"
    recordings_dir.mkdir(parents=True)
    _write_recording(recordings_dir / "nifty_20260821.jsonl")

    broker = SimulatorBroker(BrokerConfig(broker_code="SIMULATOR"), data_directory=tmp_path)
    chain = broker.get_option_chain(
        OptionChainRequest(underlying="NIFTY", exchange="NFO", expiry_date="25-Aug-2026")
    )

    assert chain.spot_price == Decimal("24200")
    assert len(chain.rows) == 1
    leg = chain.rows[0]
    assert leg.strike_price == Decimal("24200")
    assert leg.call_ltp == Decimal("120.5")
    assert leg.put_ltp == Decimal("95.25")
    assert leg.is_atm is True
    assert len(chain.calls) == 1
    assert len(chain.puts) == 1


def test_get_quotes_seeds_from_recording(tmp_path: Path) -> None:
    """SimulatorBroker.get_quotes should return the last recorded tick, not an empty Quote."""
    recordings_dir = tmp_path / "simulator" / "recordings"
    recordings_dir.mkdir(parents=True)
    _write_recording(recordings_dir / "nifty_20260821.jsonl")

    broker = SimulatorBroker(BrokerConfig(broker_code="SIMULATOR"), data_directory=tmp_path)
    quote = broker.get_quotes("NIFTY", "NSE")

    assert quote.ltp == Decimal("24200")


def test_no_recording_returns_empty_but_valid(tmp_path: Path) -> None:
    """With no recording present, should degrade to empty results rather than raise."""
    broker = SimulatorBroker(BrokerConfig(broker_code="SIMULATOR"), data_directory=tmp_path)

    chain = broker.get_option_chain(
        OptionChainRequest(underlying="NIFTY", exchange="NFO", expiry_date="25-Aug-2026")
    )
    quote = broker.get_quotes("NIFTY", "NSE")

    assert chain.rows == []
    assert quote.ltp is None
