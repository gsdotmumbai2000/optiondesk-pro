"""Public market data service API."""

from decimal import Decimal

from app.brokers.shared.enums import ProductType
from app.market_data.live.connection_state import MarketDataConnectionState
from app.market_data.live.live_provider import LiveMarketDataProvider
from app.market_data.live.market_status_detector import MarketStatusSnapshot
from app.market_data.models.tick import TickSnapshot


class MarketDataService:
    """Single source of truth for live market prices."""

    def __init__(self, provider: LiveMarketDataProvider) -> None:
        """Initialize service."""
        self._provider = provider

    @property
    def provider(self) -> LiveMarketDataProvider:
        """Return underlying live provider."""
        return self._provider

    def load_watchlist(
        self,
        symbols: tuple[str, ...],
        exchange: str = "NSE",
        *,
        product_type: ProductType = ProductType.CASH,
    ) -> None:
        """Load watchlist symbols as pending subscriptions."""
        for symbol in symbols:
            self._provider.subscriptions.register(
                symbol, exchange, product_type=product_type
            )

    def subscribe(
        self,
        symbol: str,
        exchange: str,
        *,
        product_type: ProductType = ProductType.CASH,
        expiry_date: str = "",
        strike_price: str = "",
        option_right: str = "",
    ) -> None:
        """Register symbol; broker subscribe only when connected."""
        self._provider.subscriptions.register(
            symbol,
            exchange,
            product_type=product_type,
            expiry_date=expiry_date,
            strike_price=strike_price,
            option_right=option_right,
        )

    def unsubscribe(
        self,
        symbol: str,
        exchange: str,
        *,
        product_type: ProductType = ProductType.CASH,
        expiry_date: str = "",
        strike_price: str = "",
    ) -> None:
        """Remove symbol from watchlist."""
        self._provider.subscriptions.remove(
            symbol,
            exchange,
            product_type=product_type,
            expiry_date=expiry_date,
            strike_price=strike_price,
        )

    def latest_price(self, symbol: str, exchange: str, **parts: str) -> Decimal | None:
        """Return latest price for a symbol."""
        tick = self.latest_tick(symbol, exchange, **parts)
        return tick.ltp if tick is not None else None

    def latest_tick(self, symbol: str, exchange: str, **parts: str) -> TickSnapshot | None:
        """Return latest tick snapshot (may be stale)."""
        return self._provider.tick_cache.get(exchange, symbol, **parts)

    def market_status(self) -> MarketStatusSnapshot:
        """Return current market status."""
        return self._provider.market_status.detect()

    def connection_status(self) -> MarketDataConnectionState:
        """Return market data connection state."""
        return self._provider.connection.state

    def last_tick_time(self):
        """Return timestamp of last received tick."""
        return self._provider.tick_cache.last_update

    def tick_count(self) -> int:
        """Return total ticks received."""
        return self._provider.dispatcher.tick_count
