"""Resolve broker feed identifiers to application instrument symbols."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class CanonicalSymbol:
    """Canonical symbol and its original broker-supplied identifier."""

    symbol: str
    broker_symbol: str


class SymbolCanonicalizer(Protocol):
    """Translate a broker identifier into an application symbol."""

    def canonicalize(
        self, broker_symbol: str, *, exchange: str, broker_code: str = ""
    ) -> CanonicalSymbol: ...


class _InstrumentService(Protocol):
    def find_by_symbol(self, trading_symbol: str) -> list[object]: ...

    def find_by_display_name(self, display_name: str) -> list[object]: ...

    def find_by_broker_symbol(
        self, broker_code: str, broker_symbol: str
    ) -> list[object]: ...


class InstrumentMasterSymbolCanonicalizer:
    """Resolve feed symbols using the application's Instrument Master."""

    def __init__(self, instruments: _InstrumentService | None = None) -> None:
        self._instruments = instruments

    def canonicalize(
        self, broker_symbol: str, *, exchange: str, broker_code: str = ""
    ) -> CanonicalSymbol:
        """Return the canonical master symbol, retaining the original identifier.

        Broker feeds commonly prefix their human-readable instrument name with an
        internal token (for example ``4.1!NIFTY 50``).  The token is removed only
        for master lookup; the original value is retained for diagnostics.
        """
        raw = str(broker_symbol)
        if self._instruments is None:
            return CanonicalSymbol(symbol=raw, broker_symbol=raw)

        if broker_code:
            matches = self._instruments.find_by_broker_symbol(broker_code, raw)
            if len(matches) == 1:
                return CanonicalSymbol(
                    symbol=str(getattr(matches[0], "trading_symbol")),
                    broker_symbol=raw,
                )

        for candidate in self._candidates(raw):
            matches = self._instruments.find_by_symbol(candidate)
            if len(matches) == 1:
                return CanonicalSymbol(
                    symbol=str(getattr(matches[0], "trading_symbol")),
                    broker_symbol=raw,
                )
            matches = self._instruments.find_by_display_name(candidate)
            if len(matches) == 1:
                return CanonicalSymbol(
                    symbol=str(getattr(matches[0], "trading_symbol")),
                    broker_symbol=raw,
                )
        return CanonicalSymbol(symbol=raw, broker_symbol=raw)

    @staticmethod
    def _candidates(broker_symbol: str) -> tuple[str, ...]:
        """Produce master-search candidates without broker-specific mappings."""
        stripped = broker_symbol.strip()
        label = stripped.rsplit("!", maxsplit=1)[-1].strip()
        return tuple(dict.fromkeys(candidate for candidate in (stripped, label) if candidate))
