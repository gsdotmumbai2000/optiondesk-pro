"""Calculation provider ports."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Protocol


class IMarketDataQueryPort(Protocol):
    """Read-only market data access for calculation inputs."""

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


class IInstrumentSpecificationPort(Protocol):
    """Read-only instrument specification access."""

    def get_lot_size(self, underlying: str) -> int: ...

    def get_tick_size(self, underlying: str) -> Decimal: ...

    def get_strike_interval(self, underlying: str) -> Decimal: ...


class IExpiryCalendarPort(Protocol):
    """Read-only expiry calendar access."""

    def calculate_dte(self, exchange: str, from_date: date, expiry_date: date) -> int: ...

    def calculate_tte_seconds(
        self,
        exchange: str,
        now: datetime,
        expiry_date: date,
    ) -> int: ...


class IMarketStatusPort(Protocol):
    """Read-only market status access."""

    def is_market_open(self, exchange: str, moment: datetime) -> bool: ...

    def trade_date(self, exchange: str, moment: datetime) -> date: ...
