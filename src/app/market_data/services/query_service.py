"""Market data query service."""

from datetime import datetime
from decimal import Decimal

from app.brokers.broker_interface.interface import BrokerInterface
from app.brokers.shared.enums import HistoricalInterval, ProductType
from app.brokers.shared.models import HistoricalRequest as BrokerHistoricalRequest
from app.brokers.shared.models import OptionChainRequest as BrokerOptionChainRequest
from app.market_data.cache.keys import chain_key, quote_key
from app.market_data.cache.market_cache import MarketCache
from app.market_data.history.history_manager import HistoryManager
from app.market_data.models import (
    FutureQuote,
    HistoricalBar,
    IndexQuote,
    OptionChain,
    Quote,
)
from app.market_data.normalizer.chain_normalizer import normalize_option_chain
from app.market_data.normalizer.historical_normalizer import normalize_historical_bars
from app.market_data.normalizer.quote_normalizer import normalize_quote, to_future_quote, to_index_quote
from app.market_data.snapshots.snapshot_manager import SnapshotManager
from app.market_data.validation.validators import MarketDataValidator


class MarketDataQueryService:
    """Query API for market data."""

    def __init__(
        self,
        broker: BrokerInterface,
        cache: MarketCache,
        history: HistoryManager,
        snapshots: SnapshotManager,
        validator: MarketDataValidator,
    ) -> None:
        """Initialize query service."""
        self._broker = broker
        self._cache = cache
        self._history = history
        self._snapshots = snapshots
        self._validator = validator

    def get_quote(
        self,
        symbol: str,
        exchange: str,
        *,
        expiry_date: str = "",
        product_type: str = "",
        option_right: str = "",
        strike_price: str = "",
    ) -> Quote:
        """Return latest quote from cache or broker."""
        cached = self._cache.get_quote(
            exchange,
            symbol,
            expiry_date=expiry_date,
            strike_price=strike_price,
            option_right=option_right,
        )
        if cached is not None:
            return cached
        broker_quote = self._broker.get_quotes(
            symbol,
            exchange,
            expiry_date=expiry_date,
            product_type=product_type,
            option_right=option_right,
            strike_price=strike_price,
        )
        quote = normalize_quote(
            broker_quote,
            expiry_date=expiry_date,
            strike_price=Decimal(strike_price) if strike_price else None,
            option_right=option_right,
        )
        self._validator.validate_quote(quote)
        self._cache.put_quote(quote)
        return quote

    def get_option_chain(
        self,
        underlying: str,
        exchange: str,
        expiry_date: str,
    ) -> OptionChain:
        """Return option chain from cache or broker."""
        cached = self._cache.get_chain(underlying, exchange, expiry_date)
        if cached is not None:
            return cached
        broker_chain = self._broker.get_option_chain(
            BrokerOptionChainRequest(
                underlying=underlying,
                exchange=exchange,
                expiry_date=expiry_date,
            )
        )
        chain = normalize_option_chain(broker_chain)
        self._validator.validate_chain(chain)
        self._cache.put_chain(chain)
        return chain

    def get_historical(
        self,
        symbol: str,
        exchange: str,
        *,
        from_date: datetime,
        to_date: datetime,
        interval: HistoricalInterval = HistoricalInterval.ONE_MINUTE,
        product_type: ProductType = ProductType.FUTURES,
    ) -> list[HistoricalBar]:
        """Return historical bars."""
        key = f"{exchange}:{symbol}:{interval.value}"
        cached = self._cache.get_historical(key)
        if cached is not None:
            return cached
        broker_bars = self._broker.get_historical_data(
            BrokerHistoricalRequest(
                symbol=symbol,
                exchange=exchange,
                product_type=product_type,
                interval=interval,
                from_date=from_date,
                to_date=to_date,
            )
        )
        bars = normalize_historical_bars(broker_bars, symbol=symbol, exchange=exchange)
        for bar in bars:
            self._validator.validate_bar(bar)
        self._cache.put_historical(key, bars)
        return bars

    def get_latest(self, symbol: str, exchange: str) -> Quote | None:
        """Return latest cached or historical quote."""
        key = quote_key(exchange, symbol)
        return self._cache.get_quote(exchange, symbol) or self._history.get_latest_quote(key)

    def get_snapshot(self):
        """Return current snapshot."""
        return self._snapshots.current

    def get_atm_strike(self, underlying: str, exchange: str, expiry_date: str) -> Decimal | None:
        """Return ATM strike from option chain."""
        chain = self.get_option_chain(underlying, exchange, expiry_date)
        return chain.atm_strike

    def get_future(self, symbol: str, exchange: str, expiry_date: str) -> FutureQuote:
        """Return future quote."""
        cached = self._cache.get_future(exchange, symbol, expiry_date)
        if cached is not None:
            return cached
        quote = self.get_quote(symbol, exchange, expiry_date=expiry_date, product_type="futures")
        future = to_future_quote(quote)
        self._cache.put_future(future)
        return future

    def get_spot(self, symbol: str, exchange: str) -> IndexQuote:
        """Return spot/index quote."""
        quote = self.get_quote(symbol, exchange)
        return to_index_quote(quote)

    def get_oi(self, symbol: str, exchange: str, **kwargs: str) -> int | None:
        """Return open interest for a symbol."""
        quote = self.get_quote(symbol, exchange, **kwargs)
        return quote.open_interest

    def get_volume(self, symbol: str, exchange: str, **kwargs: str) -> int | None:
        """Return volume for a symbol."""
        quote = self.get_quote(symbol, exchange, **kwargs)
        return quote.volume
