"""Reconnect handling for live market data."""

from app.logging.logging_manager import get_logger
from app.market_data.live.connection_state import MarketDataConnectionStateMachine

logger = get_logger(__name__)


class ReconnectManager:
    """Delegate reconnect lifecycle to the connection state machine."""

    def __init__(self, connection: MarketDataConnectionStateMachine) -> None:
        """Initialize reconnect manager."""
        self._connection = connection
        logger.debug("Market data reconnect manager wired to state machine")
