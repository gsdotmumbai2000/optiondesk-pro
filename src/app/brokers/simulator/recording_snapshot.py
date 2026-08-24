"""Builds REST-shaped snapshots (option chain / quote) from a recorded session.

SimulatorBroker's live tick delivery bypasses REST entirely -- ReplayEngine
feeds ticks straight into EventDispatcher -- but callers like the option
chain grid's initial load still go through BrokerInterface.get_option_chain()
/get_quotes() before any ticks have replayed. Without this, that initial
pull comes back empty and the grid never gets seeded with rows to update,
even though live ticks for those rows are already flowing. This rebuilds a
"last known" snapshot straight from the same recording file being replayed.
"""

import json
from decimal import Decimal
from pathlib import Path

from app.brokers.breeze.utilities import to_decimal, to_int
from app.brokers.shared.models import OptionChain, OptionChainLeg, OptionChainRequest, Quote


class RecordingSnapshot:
    """Lazily-loaded last-known-tick-per-symbol view of a recorded session."""

    def __init__(self, recording_path: Path | None) -> None:
        """Initialize snapshot, deferring the (potentially large) file read."""
        self._recording_path = recording_path
        self._loaded = False
        self._by_symbol: dict[str, dict] = {}

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if self._recording_path is None or not self._recording_path.exists():
            return
        with self._recording_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    tick = json.loads(line)["tick"]
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue
                symbol = tick.get("symbol")
                if symbol:
                    self._by_symbol[symbol] = tick

    def quote(self, symbol: str, exchange: str) -> Quote:
        """Return the last recorded tick for symbol as a REST-shaped Quote."""
        self._ensure_loaded()
        tick = self._by_symbol.get(symbol)
        if tick is None:
            return Quote(symbol=symbol, exchange=exchange)
        ohlc = tick.get("ohlc") or {}
        return Quote(
            symbol=symbol,
            exchange=exchange,
            ltp=to_decimal(tick.get("ltp")),
            open=to_decimal(ohlc.get("open")),
            high=to_decimal(ohlc.get("high")),
            low=to_decimal(ohlc.get("low")),
            close=to_decimal(ohlc.get("close")),
            bid=to_decimal(tick.get("bid")),
            ask=to_decimal(tick.get("ask")),
            volume=to_int(tick.get("volume")),
            open_interest=to_int(tick.get("open_interest")),
            change=to_decimal(tick.get("change")),
            change_percent=to_decimal(tick.get("change_percent")),
        )

    def option_chain(self, request: OptionChainRequest) -> OptionChain:
        """Rebuild an option chain (one merged leg per strike) from recorded ticks."""
        self._ensure_loaded()
        spot_tick = self._by_symbol.get(request.underlying)
        spot_price = to_decimal(spot_tick.get("ltp")) if spot_tick else None

        legs_by_strike: dict[Decimal, OptionChainLeg] = {}
        for tick in self._by_symbol.values():
            if tick.get("product_type") != "Options":
                continue
            expiry = tick.get("expiry_date", "")
            if request.expiry_date and expiry != request.expiry_date:
                continue
            strike = to_decimal(tick.get("strike_price"))
            if strike is None:
                continue
            leg = legs_by_strike.get(strike)
            if leg is None:
                leg = OptionChainLeg(strike_price=strike, expiry_date=expiry)
                legs_by_strike[strike] = leg
            right = str(tick.get("option_right", "")).strip().lower()
            if right == "call":
                self._apply_side(leg, tick, is_call=True)
            elif right == "put":
                self._apply_side(leg, tick, is_call=False)

        legs = sorted(legs_by_strike.values(), key=lambda item: item.strike_price)
        atm_strike = None
        if spot_price is not None and legs:
            atm_strike = min(legs, key=lambda leg: abs(leg.strike_price - spot_price)).strike_price
        for leg in legs:
            leg.is_atm = atm_strike is not None and leg.strike_price == atm_strike

        calls = [leg for leg in legs if leg.call_symbol or leg.call_ltp is not None]
        puts = [leg for leg in legs if leg.put_symbol or leg.put_ltp is not None]
        resolved_expiry = request.expiry_date or (legs[0].expiry_date if legs else "")
        return OptionChain(
            underlying=request.underlying,
            exchange=request.exchange,
            expiry_date=resolved_expiry,
            spot_price=spot_price,
            atm_strike=atm_strike,
            calls=calls,
            puts=puts,
            rows=legs,
        )

    @staticmethod
    def _apply_side(leg: OptionChainLeg, tick: dict, *, is_call: bool) -> None:
        symbol = str(tick.get("symbol", ""))
        ltp = to_decimal(tick.get("ltp"))
        bid = to_decimal(tick.get("bid"))
        ask = to_decimal(tick.get("ask"))
        oi = to_int(tick.get("open_interest"))
        volume = to_int(tick.get("volume"))
        if is_call:
            leg.call_symbol = symbol
            leg.call_ltp = ltp
            leg.call_bid = bid
            leg.call_ask = ask
            leg.call_oi = oi
            leg.call_volume = volume
        else:
            leg.put_symbol = symbol
            leg.put_ltp = ltp
            leg.put_bid = bid
            leg.put_ask = ask
            leg.put_oi = oi
            leg.put_volume = volume
