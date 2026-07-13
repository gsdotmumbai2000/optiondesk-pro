"""Live option chain service."""

from app.live.cache.option_cache import LiveOptionCache
from app.live.models.chain_key import ChainKey
from app.live.models.option_chain import LiveOptionChain
from app.live.option_chain.chain_manager import OptionChainManager
from app.market_data.models.tick import TickSnapshot


class LiveOptionChainService:
    """Public API for live option chain maintenance."""

    def __init__(self, manager: OptionChainManager, cache: LiveOptionCache) -> None:
        self._manager = manager
        self._cache = cache

    def on_tick(self, tick: TickSnapshot) -> LiveOptionChain | None:
        return self._manager.apply_tick(tick)

    def get_chain(self, underlying: str, exchange: str, expiry_date: str) -> LiveOptionChain | None:
        return self._cache.get(ChainKey(underlying, exchange, expiry_date))

    def chain_count(self) -> int:
        return self._cache._store.size()  # noqa: SLF001
