"""Enterprise market data cache."""

from threading import RLock

from app.market_data.cache.keys import chain_key, quote_key
from app.market_data.cache.lru import LruTtlCache
from app.market_data.models import FutureQuote, HistoricalBar, OptionChain, Quote


class MarketCache:
    """Thread-safe O(1) market data cache."""

    def __init__(self, *, max_quotes: int = 10_000, ttl_seconds: int = 300) -> None:
        """Initialize cache stores."""
        self._quotes = LruTtlCache[Quote](max_quotes, ttl_seconds)
        self._futures = LruTtlCache[FutureQuote](max_quotes, ttl_seconds)
        self._chains = LruTtlCache[OptionChain](1_000, ttl_seconds)
        self._historical = LruTtlCache[list[HistoricalBar]](2_000, ttl_seconds * 4)
        self._lock = RLock()

    def get_quote(self, exchange: str, symbol: str, **kwargs: str) -> Quote | None:
        """Return cached quote."""
        return self._quotes.get(quote_key(exchange, symbol, **kwargs))

    def put_quote(self, quote: Quote) -> None:
        """Store quote in cache."""
        key = quote_key(
            quote.exchange,
            quote.symbol,
            expiry_date=quote.expiry_date,
            strike_price=str(quote.strike_price or ""),
            option_right=quote.option_right,
        )
        self._quotes.put(key, quote)

    def get_future(self, exchange: str, symbol: str, expiry_date: str) -> FutureQuote | None:
        """Return cached future quote."""
        return self._futures.get(quote_key(exchange, symbol, expiry_date=expiry_date))

    def put_future(self, quote: FutureQuote) -> None:
        """Store future quote."""
        self._futures.put(
            quote_key(quote.exchange, quote.symbol, expiry_date=quote.expiry_date),
            quote,
        )

    def get_chain(self, underlying: str, exchange: str, expiry_date: str) -> OptionChain | None:
        """Return cached option chain."""
        return self._chains.get(chain_key(underlying, exchange, expiry_date))

    def put_chain(self, chain: OptionChain) -> None:
        """Store option chain."""
        self._chains.put(chain_key(chain.underlying, chain.exchange, chain.expiry_date), chain)

    def get_historical(self, key: str) -> list[HistoricalBar] | None:
        """Return cached historical bars."""
        return self._historical.get(key)

    def put_historical(self, key: str, bars: list[HistoricalBar]) -> None:
        """Store historical bars."""
        self._historical.put(key, bars)

    def invalidate_all(self) -> None:
        """Invalidate all caches."""
        with self._lock:
            self._quotes.clear()
            self._futures.clear()
            self._chains.clear()
            self._historical.clear()

    def purge_expired(self) -> int:
        """Purge expired entries from all caches."""
        return (
            self._quotes.purge_expired()
            + self._futures.purge_expired()
            + self._chains.purge_expired()
            + self._historical.purge_expired()
        )

    @property
    def quote_count(self) -> int:
        """Return number of cached quotes."""
        return self._quotes.size()

    def list_quotes(self) -> list[Quote]:
        """Return all cached quotes."""
        with self._lock:
            return [
                entry.value
                for entry in self._quotes._entries.values()  # noqa: SLF001
                if entry.value is not None
            ]
