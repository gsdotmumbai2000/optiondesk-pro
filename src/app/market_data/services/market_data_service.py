"""Public market data service API."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from app.brokers.shared.enums import ProductType
from app.logging.logging_manager import get_logger
from app.market_data.diagnostics import log_market_data_diagnostic, log_tick_diagnostic
from app.market_data.models.option import OptionChain
from app.market_data.models.tick import TickSnapshot
from app.market_data.models.live_status import MarketStatusSnapshot
from app.market_data.websocket.connection_state import MarketDataConnectionState

if TYPE_CHECKING:
    from app.market_data.providers.live_market_provider import LiveMarketDataProvider

logger = get_logger(__name__)


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
        self._provider.subscriptions.bulk_subscribe(
            ((symbol, exchange) for symbol in symbols),
            product_type=product_type,
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
        self._provider.subscriptions.subscribe(
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
        option_right: str = "",
    ) -> None:
        """Remove symbol from watchlist."""
        self._provider.subscriptions.unsubscribe(
            symbol,
            exchange,
            product_type=product_type,
            expiry_date=expiry_date,
            strike_price=strike_price,
            option_right=option_right,
        )

    def bulk_subscribe(
        self,
        symbols: tuple[tuple[str, str], ...],
        *,
        product_type: ProductType = ProductType.CASH,
    ) -> None:
        """Subscribe multiple symbols."""
        self._provider.subscriptions.bulk_subscribe(symbols, product_type=product_type)

    def bulk_unsubscribe(
        self,
        symbols: tuple[tuple[str, str], ...],
        *,
        product_type: ProductType = ProductType.CASH,
    ) -> None:
        """Unsubscribe multiple symbols."""
        self._provider.subscriptions.bulk_unsubscribe(symbols, product_type=product_type)

    def resubscribe_all(self) -> None:
        """Resubscribe all active symbols."""
        self._provider.subscriptions.resubscribe_all()

    def latest_price(self, symbol: str, exchange: str, **parts: str) -> Decimal | None:
        """Return latest price for a symbol."""
        return self._provider.cache.latest_price(exchange, symbol, **parts)

    def latest_tick(self, symbol: str, exchange: str, **parts: str) -> TickSnapshot | None:
        """Return latest tick snapshot (may be stale)."""
        tick = self._provider.cache.get_tick(exchange, symbol, **parts)
        if tick is not None:
            log_tick_diagnostic(logger, "CACHE", "cache lookup hit", tick)
        else:
            log_market_data_diagnostic(
                logger,
                "CACHE",
                "cache lookup miss",
                symbol=symbol,
                exchange=exchange,
            )
        return tick

    def get_option_chain(
        self, underlying: str, exchange: str, expiry_date: str
    ) -> OptionChain:
        """Return option chain from cache, falling back to a broker REST fetch."""
        logger.debug(
            "MarketDataService.get_option_chain: calling engine.query.get_option_chain "
            "underlying={underlying} exchange={exchange} expiry_date={expiry_date}",
            underlying=underlying,
            exchange=exchange,
            expiry_date=expiry_date,
        )
        chain = self._provider.engine.query.get_option_chain(
            underlying, exchange, expiry_date
        )
        logger.debug("MarketDataService.get_option_chain: engine.query.get_option_chain returned")
        return chain

    def market_status(self) -> MarketStatusSnapshot:
        """Return current market status."""
        return self._provider.market_status.detect()

    def connection_status(self) -> MarketDataConnectionState:
        """Return market data connection state."""
        return self._provider.connection.state

    def last_tick_time(self):
        """Return timestamp of last received tick."""
        return self._provider.cache.live.last_update

    def tick_count(self) -> int:
        """Return total ticks received."""
        return self._provider.dispatcher.tick_count

    def cache_snapshot(self) -> dict[str, TickSnapshot]:
        """Return snapshot of all cached ticks."""
        snapshot = self._provider.cache.snapshot_ticks()
        log_market_data_diagnostic(
            logger,
            "CACHE",
            "cache snapshot",
            symbol_count=len(snapshot),
        )
        return snapshot
