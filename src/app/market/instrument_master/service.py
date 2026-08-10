"""Instrument service."""

from datetime import date
from decimal import Decimal

from app.market.cache.market_cache import MarketCache
from app.market.enums import ExpiryType, InstrumentType
from app.market.expiries.models import ExpiryRecord
from app.market.instrument_master.models import Instrument
from app.market.instrument_master.validator import InstrumentValidator
from app.market.utils.strike_utils import atm_strike, nearest_strike


class InstrumentService:
    """Application service for instrument master operations."""

    def __init__(self, cache: MarketCache) -> None:
        """Initialize instrument service."""
        self._cache = cache
        self._validator = InstrumentValidator()

    def find_by_symbol(self, trading_symbol: str) -> list[Instrument]:
        """Find instruments by trading symbol."""
        return self._cache.find_by_symbol(trading_symbol)

    def find_by_display_name(self, display_name: str) -> list[Instrument]:
        """Find instruments by their canonical display name."""
        value = display_name.casefold().strip()
        return [
            instrument
            for instrument in self._cache.get_instruments()
            if instrument.display_name.casefold().strip() == value
        ]

    def find_by_broker_symbol(
        self, broker_code: str, broker_symbol: str
    ) -> list[Instrument]:
        """Find instruments by a broker-specific identifier stored in the master."""
        broker = broker_code.casefold().strip()
        value = broker_symbol.casefold().strip()
        return [
            instrument
            for instrument in self._cache.get_instruments()
            if str(instrument.broker_symbols.get(broker_code, "")).casefold().strip()
            == value
            or any(
                key.casefold().strip() == broker
                and value == str(alias).casefold().strip()
                for key, alias in instrument.broker_symbols.items()
            )
        ]

    def find_by_exchange(self, exchange: str) -> list[Instrument]:
        """Find instruments by exchange."""
        return self._cache.find_by_exchange(exchange)

    def find_by_underlying(self, underlying: str) -> list[Instrument]:
        """Find instruments by underlying."""
        return self._cache.find_by_underlying(underlying)

    def find_by_instrument_type(
        self, instrument_type: str | InstrumentType
    ) -> list[Instrument]:
        """Find instruments by type."""
        value = (
            instrument_type.value
            if isinstance(instrument_type, InstrumentType)
            else instrument_type
        )
        return self._cache.find_by_instrument_type(value)

    def get_by_id(self, instrument_id: str) -> Instrument | None:
        """Return instrument by canonical id."""
        return self._cache.get_instrument_by_id(instrument_id)

    def get_lot_size(self, underlying: str) -> int:
        """Return lot size for an underlying."""
        return self._require_underlying(underlying).specification.lot_size

    def get_tick_size(self, underlying: str) -> Decimal:
        """Return tick size for an underlying."""
        return self._require_underlying(underlying).specification.tick_size

    def get_strike_interval(self, underlying: str) -> Decimal:
        """Return strike interval for an underlying."""
        return self._require_underlying(underlying).specification.strike_interval

    def get_freeze_quantity(self, underlying: str) -> int:
        """Return freeze quantity for an underlying."""
        return self._require_underlying(underlying).specification.freeze_quantity

    def nearest_expiry(
        self,
        underlying: str,
        exchange: str,
        *,
        on_date: date,
        expiry_type: ExpiryType = ExpiryType.WEEKLY,
    ) -> ExpiryRecord | None:
        """Return nearest expiry for an underlying."""
        return self._cache.expiry_manager.nearest_expiry(
            underlying,
            exchange,
            on_date=on_date,
            expiry_type=expiry_type,
        )

    def weekly_expiry(
        self, underlying: str, exchange: str, *, on_date: date
    ) -> ExpiryRecord | None:
        """Return nearest weekly expiry."""
        return self.nearest_expiry(
            underlying,
            exchange,
            on_date=on_date,
            expiry_type=ExpiryType.WEEKLY,
        )

    def monthly_expiry(
        self, underlying: str, exchange: str, *, on_date: date
    ) -> ExpiryRecord | None:
        """Return nearest monthly expiry."""
        return self.nearest_expiry(
            underlying,
            exchange,
            on_date=on_date,
            expiry_type=ExpiryType.MONTHLY,
        )

    def atm_strike(self, underlying: str, spot: Decimal) -> Decimal:
        """Return ATM strike for an underlying."""
        return atm_strike(spot, self.get_strike_interval(underlying))

    def nearest_strike(self, underlying: str, price: Decimal) -> Decimal:
        """Return nearest valid strike."""
        return nearest_strike(price, self.get_strike_interval(underlying))

    def save(self, instrument: Instrument) -> None:
        """Validate and save an instrument."""
        self._validator.validate(instrument)
        self._cache.save_instrument(instrument)

    def _require_underlying(self, underlying: str) -> Instrument:
        """Return the primary instrument for an underlying."""
        matches = self.find_by_underlying(underlying)
        if not matches:
            raise LookupError(f"Underlying not found: {underlying}")
        return matches[0]
