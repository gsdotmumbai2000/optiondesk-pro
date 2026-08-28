"""Adapt live market data service for calculation inputs."""

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.live.cache.option_cache import LiveOptionCache
from app.live.models.chain_key import ChainKey
from app.live.option_chain.chain_builder import ChainBuilder
from app.market_data.services.market_data_service import MarketDataService


class LiveMarketQueryAdapter:
    """Read live market data, preferring the tick-driven cache (freshest)
    and falling back to a broker REST fetch when no tick has streamed in
    yet for this key -- e.g. right after subscribing, or whenever the
    websocket simply has nothing new to deliver (market closed, thin
    liquidity, or a connected-but-quiet session). Without this fallback,
    Evaluate/Optimize/AI recommendations were permanently unusable in
    exactly that situation even though the Market tab's REST-backed
    option chain already shows real data for the same underlying/expiry
    -- MarketDataService.get_option_chain() already has this fallback;
    get_spot()/get_future() previously did not."""

    def __init__(
        self,
        market_data: MarketDataService,
        option_cache: LiveOptionCache,
    ) -> None:
        self._market_data = market_data
        self._option_cache = option_cache

    def get_spot(self, symbol: str, exchange: str) -> object:
        tick = self._market_data.latest_tick(symbol, exchange)
        if tick is not None and tick.ltp is not None:
            return SimpleNamespace(ltp=tick.ltp, timestamp=tick.timestamp)
        quote = self._market_data.get_spot(symbol, exchange)
        return SimpleNamespace(ltp=quote.ltp, timestamp=quote.timestamp)

    def get_future(self, symbol: str, exchange: str, expiry_date: str) -> object:
        tick = self._market_data.latest_tick(symbol, exchange, expiry_date=expiry_date)
        if tick is not None and tick.ltp is not None:
            return SimpleNamespace(
                ltp=tick.ltp,
                underlying=symbol,
                open_interest=tick.open_interest,
                volume=tick.volume,
                timestamp=tick.timestamp,
            )
        quote = self._market_data.get_future(symbol, exchange, expiry_date)
        return SimpleNamespace(
            ltp=quote.ltp,
            underlying=quote.underlying,
            open_interest=quote.open_interest,
            volume=quote.volume,
            timestamp=quote.timestamp,
        )

    def get_option_chain(self, underlying: str, exchange: str, expiry_date: str) -> object:
        chain = self._option_cache.get(ChainKey(underlying, exchange, expiry_date))
        if chain is not None:
            return ChainBuilder.to_market_chain(chain)
        return self._market_data.get_option_chain(underlying, exchange, expiry_date)

    def get_atm_strike(self, underlying: str, exchange: str, expiry_date: str) -> Decimal | None:
        chain = self._option_cache.get(ChainKey(underlying, exchange, expiry_date))
        return chain.atm_strike if chain is not None else None
