"""Maintain live option chain from market ticks."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from threading import RLock
from typing import TYPE_CHECKING

from app.calculation.utilities.leg_greeks import compute_leg_greeks
from app.live.cache.option_cache import LiveOptionCache
from app.live.models.chain_key import ChainKey
from app.live.models.enums import ChainSide
from app.live.models.option_chain import LiveOptionChain, LiveOptionLeg, LiveOptionStrike
from app.live.validation.chain_validator import ChainValidator
from app.live.validation.tick_validator import TickValidator
from app.market_data.models.tick import TickSnapshot
from app.pricing.models.enums import OptionType

if TYPE_CHECKING:
    from app.market_data.services.market_data_service import MarketDataService

_EXPIRY_FORMATS = ("%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y")

# A liquid ATM strike can tick several times a second; solving IV (a bisection
# loop) plus pricing/Greeks on every single one -- and calling into
# MarketDataService.latest_tick() for spot on every one, which itself logs a
# diagnostic line per call -- turned out to matter at that rate. Recomputing
# is throttled to at most once per _MIN_REFRESH_INTERVAL when the price is
# actually moving, but forced at least every _MAX_STALE_INTERVAL even for a
# quiet leg so IV/Greeks don't go stale indefinitely.
_MIN_REFRESH_INTERVAL = timedelta(milliseconds=500)
_MAX_STALE_INTERVAL = timedelta(seconds=5)


def _parse_expiry(expiry_date: str) -> date | None:
    for fmt in _EXPIRY_FORMATS:
        try:
            return datetime.strptime(expiry_date, fmt).date()
        except ValueError:
            continue
    return None


class OptionChainManager:
    """Aggregate ticks into live option chains."""

    def __init__(
        self,
        cache: LiveOptionCache,
        *,
        market_data: "MarketDataService | None" = None,
        tick_validator: TickValidator | None = None,
        chain_validator: ChainValidator | None = None,
    ) -> None:
        self._cache = cache
        self._market_data = market_data
        self._tick_validator = tick_validator or TickValidator()
        self._chain_validator = chain_validator or ChainValidator()
        self._lock = RLock()
        # symbol -> (ltp used, timestamp) of the last actual Greeks solve --
        # deliberately not derived from `previous.ltp`/`previous.timestamp`,
        # since a carried-forward leg's ltp is the *current* tick's price
        # (only its Greeks are stale), so comparing against it would mask a
        # price move that happened entirely within throttled ticks.
        self._greeks_solved: dict[str, tuple[Decimal, datetime]] = {}

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
            previous = row.call if side == ChainSide.CALL else row.put
            spot = self._apply_greeks(leg, previous, key.underlying, strike, side, tick)
            if side == ChainSide.CALL:
                row.call = leg
            else:
                row.put = leg
            chain.strikes[str(strike)] = row
            if spot is not None:
                chain.spot_price = spot
            chain.updated_at = tick.timestamp or datetime.now(timezone.utc)
            self._chain_validator.validate(chain)
            self._cache.put(key, chain)
            return chain

    def _apply_greeks(
        self,
        leg: LiveOptionLeg,
        previous: LiveOptionLeg | None,
        underlying: str,
        strike: Decimal,
        side: ChainSide,
        tick: TickSnapshot,
    ) -> Decimal | None:
        """Backfill IV/Delta/Gamma/Theta/Vega on `leg` from its LTP.

        Breeze's live tick payload carries price/OI/volume only, never
        Greeks or IV, so these are solved locally via the frozen
        Black-Scholes engines rather than left blank on every tick.

        Returns the spot price used (None when neither a fresh solve nor a
        carried-forward result was available), so the caller can also use it
        to refresh `chain.spot_price` without a second lookup.
        """
        now = tick.timestamp or datetime.now(timezone.utc)
        solved = self._greeks_solved.get(leg.symbol)
        if previous is not None and previous.implied_volatility is not None and solved is not None:
            solved_ltp, solved_at = solved
            elapsed = now - solved_at
            price_unchanged = solved_ltp == leg.ltp
            if elapsed < _MAX_STALE_INTERVAL and (price_unchanged or elapsed < _MIN_REFRESH_INTERVAL):
                leg.implied_volatility = previous.implied_volatility
                leg.delta = previous.delta
                leg.gamma = previous.gamma
                leg.theta = previous.theta
                leg.vega = previous.vega
                return None

        expiry = _parse_expiry(tick.expiry_date)
        if expiry is None:
            return None
        spot = self._spot_price(underlying)
        option_type = OptionType.CALL if side == ChainSide.CALL else OptionType.PUT
        greeks = compute_leg_greeks(
            underlying=leg.underlying,
            exchange=leg.exchange,
            ltp=leg.ltp,
            spot=spot,
            strike=strike,
            expiry_date=expiry,
            option_type=option_type,
            now=now,
        )
        if greeks.implied_volatility is None:
            return spot
        leg.implied_volatility = greeks.implied_volatility
        leg.delta = greeks.delta
        leg.gamma = greeks.gamma
        leg.theta = greeks.theta
        leg.vega = greeks.vega
        self._greeks_solved[leg.symbol] = (leg.ltp, now)
        return spot

    def _spot_price(self, underlying: str) -> Decimal | None:
        if self._market_data is None:
            return None
        tick = self._market_data.latest_tick(underlying, "NSE")
        return tick.ltp if tick is not None else None

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
