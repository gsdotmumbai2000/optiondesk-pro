"""Resolve the effective broker for a MarketMode at a point in time.

AUTO mode picks the live broker on a weekday between 9:00 AM and 3:40 PM
IST, and the simulator otherwise (including all day Saturday/Sunday). This
check is evaluated on demand (app startup, or an explicit mode switch) --
it is not re-evaluated on a timer, so a session left running across the
market-open boundary stays on whatever broker was resolved last.
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo

from app.brokers.shared.enums import BrokerCode
from app.config.models.app_config import MarketMode

IST = ZoneInfo("Asia/Kolkata")
LIVE_WINDOW_START = time(9, 0)
LIVE_WINDOW_END = time(15, 40)


def is_within_live_window(now: datetime | None = None) -> bool:
    """Return True on a weekday between 9:00 AM and 3:40 PM IST."""
    moment = (now or datetime.now(IST)).astimezone(IST)
    if moment.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    return LIVE_WINDOW_START <= moment.time() <= LIVE_WINDOW_END


def resolve_effective_broker_code(
    mode: MarketMode,
    live_broker_code: str,
    *,
    now: datetime | None = None,
) -> str:
    """Return which broker code should actually be active for `mode`."""
    if mode == MarketMode.LIVE:
        return live_broker_code.upper()
    if mode == MarketMode.SIMULATOR:
        return BrokerCode.SIMULATOR.value
    return (
        live_broker_code.upper()
        if is_within_live_window(now)
        else BrokerCode.SIMULATOR.value
    )
