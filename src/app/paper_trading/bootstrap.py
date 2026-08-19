"""Paper trading bootstrap."""

from app.paper_trading.services.paper_trading_service import PaperTradingService


class PaperTradingProvider:
    """Wire paper trading dependencies."""

    def __init__(self) -> None:
        """Initialize provider."""
        self.service = PaperTradingService()
