"""Adapt live market data service for calculation inputs."""

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.live.cache.option_cache import LiveOptionCache
from app.live.models.chain_key import ChainKey
from app.live.option_chain.chain_builder import ChainBuilder
from app.logging.logging_manager import get_logger
from app.market_data.cache.keys import quote_key
from app.market_data.services.market_data_service import MarketDataService

logger = get_logger(__name__)


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
            self._log_spot_lookup_failure(symbol, exchange)
            return SimpleNamespace(ltp=None, timestamp=None)
        return SimpleNamespace(ltp=tick.ltp, timestamp=tick.timestamp)

    def _log_spot_lookup_failure(self, symbol: str, exchange: str) -> None:
        """TEMPORARY DIAGNOSTIC (NIFTY spot-unavailable trace) - boundary 4.

        Logs the requested spot lookup key alongside whatever quote keys
        are actually present in the live tick cache, so a mismatch (e.g.
        "NIFTY" vs "NIFTY 50") is visible without altering lookup behavior.
        """
        requested_key = quote_key(exchange, symbol)
        try:
            available_keys = list(self._market_data.cache_snapshot().keys())
        except Exception:
            available_keys = []
        prefix = symbol.split(" ")[0].upper()
        candidates = [key for key in available_keys if prefix in key.upper()]
        logger.debug(
            "[DIAG-4 SPOT-LOOKUP-FAIL] requested_symbol={symbol!r} requested_exchange={exchange!r} "
            "requested_key={requested_key!r} available_key_count={count} matching_candidates={candidates!r}",
            symbol=symbol,
            exchange=exchange,
            requested_key=requested_key,
            count=len(available_keys),
            candidates=candidates[:10],
        )

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
