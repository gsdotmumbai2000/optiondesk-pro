"""Maintain live option chain from market ticks."""

from datetime import datetime, timezone
from decimal import Decimal
from threading import RLock

from app.live.cache.option_cache import LiveOptionCache
from app.live.models.chain_key import ChainKey
from app.live.models.enums import ChainSide
from app.live.models.option_chain import LiveOptionChain, LiveOptionLeg, LiveOptionStrike
from app.live.validation.chain_validator import ChainValidator
from app.live.validation.tick_validator import TickValidator
from app.market_data.models.tick import TickSnapshot


class OptionChainManager:
    """Aggregate ticks into live option chains."""

    def __init__(
        self,
        cache: LiveOptionCache,
        *,
        tick_validator: TickValidator | None = None,
        chain_validator: ChainValidator | None = None,
    ) -> None:
        self._cache = cache
        self._tick_validator = tick_validator or TickValidator()
        self._chain_validator = chain_validator or ChainValidator()
        self._lock = RLock()

    def apply_tick(self, tick: TickSnapshot) -> LiveOptionChain | None:
        """Update chain from a market tick."""
        self._tick_validator.validate(tick)
        if not self._is_option_tick(tick):
            return None
        return self._apply_option_tick(tick)

    def get_chain(self, key: ChainKey) -> LiveOptionChain | None:
        return self._cache.get(key)

    def _apply_option_tick(self, tick: TickSnapshot) -> LiveOptionChain | None:
        key = ChainKey(self._underlying(tick), tick.exchange, tick.expiry_date)
        side = self._side(tick.option_right)
        strike = Decimal(str(tick.strike_price))
        leg = LiveOptionLeg(
            symbol=tick.symbol,
            exchange=tick.exchange,
            underlying=key.underlying,
            strike_price=strike,
            expiry_date=tick.expiry_date,
            side=side,
            ltp=tick.ltp,
            bid=tick.bid,
            ask=tick.ask,
            volume=tick.volume,
            open_interest=tick.open_interest,
            timestamp=tick.timestamp,
        )
        with self._lock:
            chain = self._cache.get(key) or self._empty_chain(key)
            row = chain.strikes.get(str(strike)) or LiveOptionStrike(strike_price=strike)
            if side == ChainSide.CALL:
                row.call = leg
            else:
                row.put = leg
            chain.strikes[str(strike)] = row
            chain.updated_at = tick.timestamp or datetime.now(timezone.utc)
            self._chain_validator.validate(chain)
            self._cache.put(key, chain)
            return chain

    @staticmethod
    def _empty_chain(key: ChainKey) -> LiveOptionChain:
        return LiveOptionChain(
            underlying=key.underlying,
            exchange=key.exchange,
            expiry_date=key.expiry_date,
        )

    @staticmethod
    def _is_option_tick(tick: TickSnapshot) -> bool:
        product = tick.product_type.upper()
        return bool(tick.strike_price) or product in {"OPTIONS", "OPTION"}

    @staticmethod
    def _underlying(tick: TickSnapshot) -> str:
        return tick.symbol.split("-")[0] if "-" in tick.symbol else tick.symbol

    @staticmethod
    def _side(option_right: str) -> ChainSide:
        return ChainSide.PUT if option_right.upper().startswith("P") else ChainSide.CALL
