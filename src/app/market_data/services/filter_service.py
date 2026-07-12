"""Market data search and filter service."""

from decimal import Decimal

from app.market_data.cache.market_cache import MarketCache
from app.market_data.models import OptionChain, Quote


class MarketDataFilterService:
    """Search and filter market data."""

    def __init__(self, cache: MarketCache) -> None:
        """Initialize filter service."""
        self._cache = cache

    def find_by_symbol(self, symbol: str) -> list[Quote]:
        """Find quotes by symbol."""
        symbol = symbol.upper()
        return [q for q in self._cache.list_quotes() if q.symbol.upper() == symbol]

    def find_by_exchange(self, exchange: str) -> list[Quote]:
        """Find quotes by exchange."""
        code = exchange.upper()
        return [q for q in self._cache.list_quotes() if q.exchange.upper() == code]

    def find_by_underlying(self, underlying: str) -> list[Quote]:
        """Find quotes by underlying."""
        symbol = underlying.upper()
        return [q for q in self._cache.list_quotes() if q.underlying.upper() == symbol]

    def filter_by_volume(self, quotes: list[Quote], *, min_volume: int) -> list[Quote]:
        """Filter quotes by minimum volume."""
        return [q for q in quotes if (q.volume or 0) >= min_volume]

    def filter_by_oi(self, quotes: list[Quote], *, min_oi: int) -> list[Quote]:
        """Filter quotes by minimum open interest."""
        return [q for q in quotes if (q.open_interest or 0) >= min_oi]

    def filter_chain_by_iv(
        self,
        chain: OptionChain,
        *,
        min_iv: Decimal,
    ) -> OptionChain:
        """Filter option chain strikes by IV."""
        strikes = [
            strike
            for strike in chain.strikes
            if (strike.call_iv or Decimal("0")) >= min_iv
            or (strike.put_iv or Decimal("0")) >= min_iv
        ]
        return chain.model_copy(update={"strikes": strikes})
