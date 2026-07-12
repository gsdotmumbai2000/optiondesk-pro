"""Instrument repository port."""

from typing import Protocol, runtime_checkable

from app.market.instrument_master.models import Instrument


@runtime_checkable
class IInstrumentRepository(Protocol):
    """Persistence port for instruments and underlyings."""

    def initialize(self) -> None:
        """Load or connect to storage."""

    def close(self) -> None:
        """Release storage resources."""

    def get_all(self) -> list[Instrument]:
        """Return all instruments."""

    def get_by_id(self, instrument_id: str) -> Instrument | None:
        """Return an instrument by canonical id."""

    def get_by_symbol(self, trading_symbol: str) -> list[Instrument]:
        """Return instruments matching a trading symbol."""

    def get_by_exchange(self, exchange: str) -> list[Instrument]:
        """Return instruments for an exchange."""

    def get_by_underlying(self, underlying: str) -> list[Instrument]:
        """Return instruments for an underlying."""

    def get_by_instrument_type(self, instrument_type: str) -> list[Instrument]:
        """Return instruments of a given type."""

    def save(self, instrument: Instrument) -> None:
        """Persist an instrument."""

    def save_all(self, instruments: list[Instrument]) -> None:
        """Persist multiple instruments."""
