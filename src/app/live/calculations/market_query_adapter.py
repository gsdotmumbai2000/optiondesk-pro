"""Adapt live market data service for calculation inputs."""

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.live.cache.option_cache import LiveOptionCache
from app.live.models.chain_key import ChainKey
from app.live.option_chain.chain_builder import ChainBuilder
from app.market_data.services.market_data_service import MarketDataService


class LiveMarketQueryAdapter:
    """Read-only market query backed by live caches only."""

    def __init__(
        self,
        market_data: MarketDataService,
        option_cache: LiveOptionCache,
    ) -> None:
        self._market_data = market_data
        self._option_cache = option_cache

    def get_spot(self, symbol: str, exchange: str) -> object:
        tick = self._market_data.latest_tick(symbol, exchange)
        if tick is None or tick.ltp is None:
            return SimpleNamespace(ltp=None, timestamp=None)
        return SimpleNamespace(ltp=tick.ltp, timestamp=tick.timestamp)

    def get_future(self, symbol: str, exchange: str, expiry_date: str) -> object:
        tick = self._market_data.latest_tick(
            symbol, exchange, expiry_date=expiry_date, product_type="FUTURES"
        )
        if tick is None:
            return SimpleNamespace(ltp=None, underlying=symbol, timestamp=None)
        return SimpleNamespace(
            ltp=tick.ltp,
            underlying=symbol,
            open_interest=tick.open_interest,
            volume=tick.volume,
            timestamp=tick.timestamp,
        )

    def get_option_chain(self, underlying: str, exchange: str, expiry_date: str) -> object:
        chain = self._option_cache.get(ChainKey(underlying, exchange, expiry_date))
        if chain is None:
            return SimpleNamespace(
                underlying=underlying,
                exchange=exchange,
                expiry_date=expiry_date,
                spot_price=None,
                atm_strike=None,
                strikes=[],
            )
        return ChainBuilder.to_market_chain(chain)

    def get_atm_strike(self, underlying: str, exchange: str, expiry_date: str) -> Decimal | None:
        chain = self._option_cache.get(ChainKey(underlying, exchange, expiry_date))
        return chain.atm_strike if chain is not None else None
