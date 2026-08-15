"""Port adapters for frozen upstream modules."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Protocol

from app.calculation.providers.ports import (
    IExpiryCalendarPort,
    IInstrumentSpecificationPort,
    IMarketDataQueryPort,
    IMarketStatusPort,
)


class _MarketDataQueryLike(Protocol):
    """Minimal market data query surface."""

    def get_spot(self, symbol: str, exchange: str) -> Any: ...

    def get_future(self, symbol: str, exchange: str, expiry_date: str) -> Any: ...

    def get_option_chain(
        self,
        underlying: str,
        exchange: str,
        expiry_date: str,
    ) -> Any: ...

    def get_atm_strike(
        self,
        underlying: str,
        exchange: str,
        expiry_date: str,
    ) -> Decimal | None: ...


class _InstrumentServiceLike(Protocol):
    """Minimal instrument service surface."""

    def get_lot_size(self, underlying: str) -> int: ...

    def get_tick_size(self, underlying: str) -> Decimal: ...

    def get_strike_interval(self, underlying: str) -> Decimal: ...


class _ExpiryManagerLike(Protocol):
    """Minimal expiry manager surface."""

    def calculate_dte(self, exchange: str, from_date: date, expiry_date: date) -> int: ...

    def calculate_tte(
        self,
        exchange: str,
        now: datetime,
        expiry_date: date,
    ) -> int: ...

    def nearest_expiry(
        self,
        underlying: str,
        exchange: str,
        *,
        on_date: date,
        expiry_type: Any = None,
    ) -> Any: ...


# The calculation layer speaks the broker-facing derivatives exchange code
# ("NFO"), while ExpiryService (app.market) speaks its own ExchangeCode
# ("NSEFO") -- this adapter is the boundary, so the translation belongs here
# rather than leaking either convention into the other layer.
_MARKET_EXCHANGE_CODE: dict[str, str] = {"NFO": "NSEFO", "BFO": "BSEFO"}


def _market_exchange_code(exchange: str) -> str:
    return _MARKET_EXCHANGE_CODE.get(exchange.strip().upper(), exchange)


class _MarketCalendarLike(Protocol):
    """Minimal market calendar surface."""

    def is_market_open(self, exchange: str, moment: datetime) -> bool: ...


class MarketDataQueryPortAdapter:
    """Adapt market data query service to calculation port."""

    def __init__(self, query_service: _MarketDataQueryLike) -> None:
        """Initialize adapter."""
        self._query = query_service

    def get_spot(self, symbol: str, exchange: str) -> Any:
        """Return spot quote."""
        return self._query.get_spot(symbol, exchange)

    def get_future(self, symbol: str, exchange: str, expiry_date: str) -> Any:
        """Return future quote."""
        return self._query.get_future(symbol, exchange, expiry_date)

    def get_option_chain(
        self,
        underlying: str,
        exchange: str,
        expiry_date: str,
    ) -> Any:
        """Return option chain."""
        return self._query.get_option_chain(underlying, exchange, expiry_date)

    def get_atm_strike(
        self,
        underlying: str,
        exchange: str,
        expiry_date: str,
    ) -> Decimal | None:
        """Return ATM strike."""
        return self._query.get_atm_strike(underlying, exchange, expiry_date)


class InstrumentSpecificationPortAdapter:
    """Adapt instrument service to calculation port."""

    def __init__(self, instrument_service: _InstrumentServiceLike) -> None:
        """Initialize adapter."""
        self._instruments = instrument_service

    def get_lot_size(self, underlying: str) -> int:
        """Return lot size."""
        return self._instruments.get_lot_size(underlying)

    def get_tick_size(self, underlying: str) -> Decimal:
        """Return tick size."""
        return self._instruments.get_tick_size(underlying)

    def get_strike_interval(self, underlying: str) -> Decimal:
        """Return strike interval."""
        return self._instruments.get_strike_interval(underlying)


class ExpiryCalendarPortAdapter:
    """Adapt expiry manager to calculation port."""

    def __init__(self, expiry_manager: _ExpiryManagerLike) -> None:
        """Initialize adapter."""
        self._expiry = expiry_manager

    def calculate_dte(self, exchange: str, from_date: date, expiry_date: date) -> int:
        """Return trading days to expiry."""
        return self._expiry.calculate_dte(exchange, from_date, expiry_date)

    def calculate_tte_seconds(
        self,
        exchange: str,
        now: datetime,
        expiry_date: date,
    ) -> int:
        """Return seconds to expiry."""
        return self._expiry.calculate_tte(exchange, now, expiry_date)

    def nearest_monthly_expiry(
        self,
        underlying: str,
        exchange: str,
        on_date: date,
    ) -> date | None:
        """Return the nearest monthly futures expiry, independent of any
        weekly option expiry for the same underlying/exchange."""
        from app.market.enums import ExpiryType

        record = self._expiry.nearest_expiry(
            underlying,
            _market_exchange_code(exchange),
            on_date=on_date,
            expiry_type=ExpiryType.MONTHLY,
        )
        return record.expiry_date if record is not None else None


class MarketStatusPortAdapter:
    """Adapt market calendar service to calculation port."""

    def __init__(self, calendar_service: _MarketCalendarLike) -> None:
        """Initialize adapter."""
        self._calendar = calendar_service

    def is_market_open(self, exchange: str, moment: datetime) -> bool:
        """Return whether market is open."""
        return self._calendar.is_market_open(exchange, moment)

    def trade_date(self, exchange: str, moment: datetime) -> date:
        """Return trade date for a moment."""
        return moment.date()
