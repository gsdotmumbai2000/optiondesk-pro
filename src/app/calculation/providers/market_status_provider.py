"""Market status provider."""

from datetime import datetime

from app.calculation.models.enums import MarketSessionType
from app.calculation.models.market_session import MarketSession
from app.calculation.providers.ports import IMarketStatusPort
from app.calculation.providers.time_provider import TimeProvider


class MarketStatusProvider:
    """Supply market status and session."""

    def __init__(
        self,
        market_status: IMarketStatusPort,
        time_provider: TimeProvider | None = None,
    ) -> None:
        """Initialize provider."""
        self._market_status = market_status
        self._time_provider = time_provider or TimeProvider()

    def session(self, exchange: str, moment: datetime | None = None) -> MarketSession:
        """Return market session snapshot."""
        current = moment or self._time_provider.now()
        is_open = self._market_status.is_market_open(exchange, current)
        trade_date = self._market_status.trade_date(exchange, current)
        session_type = MarketSessionType.REGULAR if is_open else MarketSessionType.CLOSED
        return MarketSession(
            exchange=exchange.upper(),
            session_type=session_type,
            is_open=is_open,
            trade_date=trade_date.isoformat(),
        )

    def status_label(self, exchange: str, moment: datetime | None = None) -> str:
        """Return market status label."""
        session = self.session(exchange, moment)
        return "OPEN" if session.is_open else "CLOSED"
