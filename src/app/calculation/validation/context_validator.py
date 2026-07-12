"""Calculation context validator."""

from datetime import datetime
from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.exceptions import InvalidContextException
from app.calculation.utilities.normalize_utils import (
    normalize_interest_rate,
    normalize_price,
    normalize_volatility,
)


class ContextValidator:
    """Validate calculation contexts before use."""

    _VALID_MARKET_STATUS = frozenset({"OPEN", "CLOSED"})

    def validate(self, context: CalculationContext) -> None:
        """Validate a complete calculation context."""
        self._validate_expiry(context.expiry, context.trade_date)
        self._validate_rate(context.interest_rate, "interest_rate")
        self._validate_rate(context.risk_free_rate, "risk_free_rate")
        self._validate_rate(context.dividend_yield, "dividend_yield")
        self._validate_volatility(context.volatility)
        self._validate_price(context.spot_price, "spot_price")
        if context.future_price is not None:
            self._validate_price(context.future_price, "future_price")
        self._validate_price(context.atm_strike, "atm_strike")
        self._validate_lot_size(context.lot_size)
        self._validate_tick_size(context.tick_size)
        self._validate_market_status(context.market_status)
        self._validate_timestamp(context.calculation_timestamp)

    def _validate_expiry(self, expiry, trade_date) -> None:
        if expiry < trade_date:
            raise InvalidContextException("expiry cannot be before trade date")

    def _validate_rate(self, value: Decimal, field: str) -> None:
        try:
            normalize_interest_rate(value)
        except InvalidContextException as error:
            raise InvalidContextException(f"{field}: {error}") from error

    def _validate_volatility(self, value: Decimal) -> None:
        try:
            normalize_volatility(value)
        except InvalidContextException as error:
            raise InvalidContextException(f"volatility: {error}") from error

    def _validate_price(self, value: Decimal, field: str) -> None:
        try:
            normalize_price(value)
        except InvalidContextException as error:
            raise InvalidContextException(f"{field}: {error}") from error

    def _validate_lot_size(self, value: int) -> None:
        if value <= 0:
            raise InvalidContextException("lot_size must be positive")

    def _validate_tick_size(self, value: Decimal) -> None:
        if value <= 0:
            raise InvalidContextException("tick_size must be positive")

    def _validate_market_status(self, value: str) -> None:
        if value not in self._VALID_MARKET_STATUS:
            raise InvalidContextException("market_status must be OPEN or CLOSED")

    def _validate_timestamp(self, value: datetime) -> None:
        if value.tzinfo is None:
            raise InvalidContextException("calculation_timestamp must be timezone-aware")
