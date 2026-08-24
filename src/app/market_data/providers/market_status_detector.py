"""Detect exchange market status for live data."""

from datetime import datetime, time
from zoneinfo import ZoneInfo

from app.brokers.broker_interface.interface import BrokerInterface
from app.market_data.models.live_status import LiveMarketStatus, MarketStatusSnapshot
from app.market_data.websocket.enums import LiveConnectionStatus
from app.market_data.websocket.websocket_service import WebSocketService

IST = ZoneInfo("Asia/Kolkata")
NSE_OPEN = time(9, 15)
NSE_CLOSE = time(15, 30)
NSE_PRE_OPEN = time(9, 0)


class MarketStatusDetector:
    """Detect pre-open, open, closed, holiday, and connection lost."""

    def __init__(
        self,
        broker: BrokerInterface,
        websocket: WebSocketService,
        *,
        exchange: str = "NSE",
        holidays: set[str] | None = None,
        always_open: bool = False,
    ) -> None:
        """Initialize detector.

        ``always_open`` bypasses the real IST wall-clock/weekday/holiday
        check for the simulator broker, which replays ticks after hours and
        would otherwise always be reported CLOSED regardless of whether it
        is actively streaming.
        """
        self._broker = broker
        self._websocket = websocket
        self._exchange = exchange
        self._holidays = holidays or set()
        self._always_open = always_open

    def detect(self) -> MarketStatusSnapshot:
        """Return current market status."""
        now = datetime.now(IST)
        trade_date = now.strftime("%Y-%m-%d")
        if not self._broker.is_connected():
            return MarketStatusSnapshot(
                LiveMarketStatus.CONNECTION_LOST, self._exchange, trade_date
            )
        if self._websocket.status == LiveConnectionStatus.DISCONNECTED:
            return MarketStatusSnapshot(
                LiveMarketStatus.CONNECTION_LOST, self._exchange, trade_date
            )
        if self._always_open:
            return MarketStatusSnapshot(LiveMarketStatus.OPEN, self._exchange, trade_date)
        if trade_date in self._holidays or now.weekday() >= 5:
            return MarketStatusSnapshot(
                LiveMarketStatus.HOLIDAY, self._exchange, trade_date, is_holiday=True
            )
        current = now.time()
        if NSE_PRE_OPEN <= current < NSE_OPEN:
            return MarketStatusSnapshot(LiveMarketStatus.PRE_OPEN, self._exchange, trade_date)
        if NSE_OPEN <= current <= NSE_CLOSE:
            return MarketStatusSnapshot(LiveMarketStatus.OPEN, self._exchange, trade_date)
        return MarketStatusSnapshot(LiveMarketStatus.CLOSED, self._exchange, trade_date)
