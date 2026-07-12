"""Pricing input validation."""

from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.pricing.exceptions import ExpiredContractException, InvalidPricingInput
from app.pricing.models.enums import ExerciseStyle
from app.pricing.models.option_contract import OptionContract


class PricingValidator:
    """Validate calculation context and option contract for pricing."""

    _MIN_TIME = Decimal("0.000001")

    def validate(self, context: CalculationContext, contract: OptionContract) -> None:
        """Validate pricing inputs."""
        self._validate_spot(context.spot_price)
        self._validate_strike(contract.strike)
        self._validate_volatility(context.volatility)
        self._validate_rate(context.risk_free_rate, "risk_free_rate")
        self._validate_rate(context.interest_rate, "interest_rate")
        self._validate_dividend(context.dividend_yield)
        self._validate_time_to_expiry(context.time_to_expiry)
        self._validate_exercise_style(contract.exercise_style)
        self._validate_expiry_alignment(context, contract)
        self._validate_multiplier(contract.multiplier)

    def _validate_spot(self, value: Decimal) -> None:
        if value <= 0:
            raise InvalidPricingInput("spot_price must be positive")

    def _validate_strike(self, value: Decimal) -> None:
        if value <= 0:
            raise InvalidPricingInput("strike must be positive")

    def _validate_volatility(self, value: Decimal) -> None:
        if value <= 0:
            raise InvalidPricingInput("volatility must be positive")

    def _validate_rate(self, value: Decimal, field: str) -> None:
        if value < 0:
            raise InvalidPricingInput(f"{field} cannot be negative")

    def _validate_dividend(self, value: Decimal) -> None:
        if value < 0:
            raise InvalidPricingInput("dividend_yield cannot be negative")

    def _validate_time_to_expiry(self, value: Decimal) -> None:
        if value <= 0:
            raise ExpiredContractException("time_to_expiry must be positive")
        if value < self._MIN_TIME:
            raise ExpiredContractException("contract is effectively expired")

    def _validate_exercise_style(self, style: ExerciseStyle) -> None:
        if style != ExerciseStyle.EUROPEAN:
            raise InvalidPricingInput("only European exercise style is supported")

    def _validate_expiry_alignment(
        self,
        context: CalculationContext,
        contract: OptionContract,
    ) -> None:
        if contract.expiry != context.expiry:
            raise InvalidPricingInput("contract expiry must match calculation context expiry")

    def _validate_multiplier(self, value: int) -> None:
        if value <= 0:
            raise InvalidPricingInput("multiplier must be positive")
