"""Resolve broker feed identifiers to application instrument symbols."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
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


# Breeze sends abbreviated index display names on the tick feed that don't
# match the Instrument Master's full display names (e.g. "NIFTY FIN SERVICE"
# vs "NIFTY Financial Services"). This explicit, case-insensitive alias map
# resolves those known broker abbreviations to the application's canonical
# symbols without introducing fuzzy/partial matching. Keys are casefolded.
_BROKER_DISPLAY_NAME_ALIASES: dict[str, str] = {
    "nifty fin service": "FINNIFTY",
    "nifty mid select": "MIDCPNIFTY",
}


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

        if self._instruments is not None:
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

        alias = self._resolve_alias(raw)
        if alias is not None:
            return CanonicalSymbol(symbol=alias, broker_symbol=raw)

        return CanonicalSymbol(symbol=raw, broker_symbol=raw)

    @classmethod
    def _resolve_alias(cls, broker_symbol: str) -> str | None:
        """Resolve a known Breeze abbreviated display name to a canonical symbol."""
        for candidate in cls._candidates(broker_symbol):
            alias = _BROKER_DISPLAY_NAME_ALIASES.get(candidate.strip().casefold())
            if alias is not None:
                return alias
        return None

    @staticmethod
    def _candidates(broker_symbol: str) -> tuple[str, ...]:
        """Produce master-search candidates without broker-specific mappings."""
        stripped = broker_symbol.strip()
        label = stripped.rsplit("!", maxsplit=1)[-1].strip()
        return tuple(dict.fromkeys(candidate for candidate in (stripped, label) if candidate))


def build_option_contract_symbol(
    underlying: str, expiry_date: str, strike_price: str, option_right: str
) -> str:
    """Build a deterministic canonical option contract symbol.

    Breeze's streaming option ticks identify the contract with an opaque
    internal token (e.g. ``4.1!51219``) rather than a stable trading symbol.
    This builds one from the already-canonical underlying plus the tick's
    own expiry/strike/right fields, e.g.::

        build_option_contract_symbol("NIFTY", "13-Feb-2026", "24500", "Call")
        -> "NIFTY-13-Feb-2026-24500-CE"
    """
    side = "PE" if option_right.strip().upper().startswith("P") else "CE"
    return f"{underlying}-{expiry_date.strip()}-{_format_strike(strike_price)}-{side}"


def _format_strike(strike_price: str) -> str:
    """Render a strike price without a redundant trailing ``.0``."""
    try:
        value = Decimal(str(strike_price))
    except (InvalidOperation, ValueError):
        return str(strike_price).strip()
    if value == value.to_integral_value():
        return str(int(value))
    return format(value.normalize(), "f")
