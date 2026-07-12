"""Market data validators."""

from datetime import datetime, timezone
from decimal import Decimal

from app.market_data.models import HistoricalBar, OptionChain, Quote
from app.market_data.validation.exceptions import MarketDataValidationException


class MarketDataValidator:
    """Validate enterprise market data objects."""

    def validate_quote(self, quote: Quote) -> None:
        """Validate a quote."""
        if not quote.symbol.strip():
            raise MarketDataValidationException("symbol is required")
        if not quote.exchange.strip():
            raise MarketDataValidationException("exchange is required")
        self._validate_price(quote.ltp, "ltp")
        self._validate_volume(quote.volume)
        self._validate_oi(quote.open_interest)
        self._validate_timestamp(quote.timestamp)

    def validate_chain(self, chain: OptionChain) -> None:
        """Validate an option chain."""
        if not chain.underlying.strip():
            raise MarketDataValidationException("underlying is required")
        if not chain.expiry_date.strip():
            raise MarketDataValidationException("expiry_date is required")
        for strike in chain.strikes:
            self._validate_strike(strike.strike_price)
            self._validate_oi(strike.call_oi)
            self._validate_oi(strike.put_oi)

    def validate_bar(self, bar: HistoricalBar) -> None:
        """Validate a historical bar."""
        self._validate_timestamp(bar.timestamp)
        self._validate_price(bar.open, "open")
        self._validate_price(bar.high, "high")
        self._validate_price(bar.low, "low")
        self._validate_price(bar.close, "close")
        self._validate_volume(bar.volume)

    def _validate_price(self, value: Decimal | None, field: str) -> None:
        if value is not None and value < 0:
            raise MarketDataValidationException(f"{field} cannot be negative")

    def _validate_volume(self, value: int | None) -> None:
        if value is not None and value < 0:
            raise MarketDataValidationException("volume cannot be negative")

    def _validate_oi(self, value: int | None) -> None:
        if value is not None and value < 0:
            raise MarketDataValidationException("open_interest cannot be negative")

    def _validate_strike(self, value: Decimal) -> None:
        if value <= 0:
            raise MarketDataValidationException("strike_price must be positive")

    def _validate_timestamp(self, value: datetime | None) -> None:
        if value is not None and value > datetime.now(timezone.utc):
            raise MarketDataValidationException("timestamp cannot be in the future")
