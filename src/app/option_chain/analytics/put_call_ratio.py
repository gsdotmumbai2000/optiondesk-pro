"""Put/call ratio analytics."""

from decimal import Decimal

from app.calculation.models.snapshots import OptionChainSnapshot


def put_call_ratio(option_chain: OptionChainSnapshot) -> tuple[Decimal, int, int]:
    """Return put/call ratio and aggregate open interest."""
    call_oi = sum(strike.call_oi or 0 for strike in option_chain.strikes)
    put_oi = sum(strike.put_oi or 0 for strike in option_chain.strikes)
    if call_oi <= 0:
        return Decimal("1"), call_oi, put_oi
    return Decimal(put_oi) / Decimal(call_oi), call_oi, put_oi
