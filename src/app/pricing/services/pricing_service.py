"""Pricing application service."""

from app.calculation.context.calculation_context import CalculationContext
from app.pricing.black_scholes.engine import BlackScholesEngine
from app.pricing.models.option_contract import OptionContract
from app.pricing.models.pricing_result import PricingResult
from app.pricing.validation.pricing_validator import PricingValidator


class PricingService:
    """Orchestrate validation and Black-Scholes pricing."""

    def __init__(
        self,
        engine: BlackScholesEngine | None = None,
        validator: PricingValidator | None = None,
    ) -> None:
        """Initialize pricing service."""
        self._engine = engine or BlackScholesEngine()
        self._validator = validator or PricingValidator()

    @property
    def engine(self) -> BlackScholesEngine:
        """Return pricing engine."""
        return self._engine

    @property
    def validator(self) -> PricingValidator:
        """Return pricing validator."""
        return self._validator

    def price(
        self,
        context: CalculationContext,
        contract: OptionContract,
    ) -> PricingResult:
        """Price a single European option."""
        self._validator.validate(context, contract)
        return self._engine.price(context, contract)

    def price_many(
        self,
        context: CalculationContext,
        contracts: tuple[OptionContract, ...],
    ) -> tuple[PricingResult, ...]:
        """Price multiple contracts with shared context terms."""
        for contract in contracts:
            self._validator.validate(context, contract)
        return self._engine.price_many(context, contracts)
