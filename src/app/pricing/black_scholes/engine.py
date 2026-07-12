"""Black-Scholes pricing engine."""

from datetime import datetime, timezone
from decimal import Decimal

from app.calculation.context.calculation_context import CalculationContext
from app.pricing.black_scholes import formulas
from app.pricing.black_scholes.intermediates import BSContextTerms, BSStrikeTerms
from app.pricing.models.enums import ModelVersion, OptionType
from app.pricing.models.option_contract import OptionContract
from app.pricing.models.pricing_result import PricingResult
from app.pricing.utilities.decimal_utils import to_decimal, to_float
from app.pricing.utilities.intrinsic import intrinsic_value


class BlackScholesEngine:
    """European Black-Scholes-Merton pricing engine."""

    def price(
        self,
        context: CalculationContext,
        contract: OptionContract,
        *,
        context_terms: BSContextTerms | None = None,
    ) -> PricingResult:
        """Price a single European option contract."""
        terms = context_terms or BSContextTerms.from_context(context)
        strike = to_float(contract.strike)
        strike_terms = BSStrikeTerms.from_context_terms(terms, strike)
        theoretical = self._theoretical_price(contract.option_type, terms, strike_terms)
        intrinsic = intrinsic_value(context.spot_price, contract.strike, contract.option_type)
        extrinsic = max(theoretical - intrinsic, to_decimal(0.0))
        scaled = theoretical * to_decimal(contract.multiplier)
        return PricingResult(
            theoretical_price=scaled,
            intrinsic_value=intrinsic * to_decimal(contract.multiplier),
            extrinsic_value=extrinsic * to_decimal(contract.multiplier),
            d1=to_decimal(strike_terms.d1),
            d2=to_decimal(strike_terms.d2),
            forward_price=to_decimal(terms.forward_price),
            discount_factor=to_decimal(terms.discount_factor),
            calculation_time=datetime.now(timezone.utc),
            model_version=ModelVersion.BLACK_SCHOLES_MERTON_V1,
        )

    def price_many(
        self,
        context: CalculationContext,
        contracts: tuple[OptionContract, ...],
    ) -> tuple[PricingResult, ...]:
        """Price multiple contracts reusing context intermediates."""
        terms = BSContextTerms.from_context(context)
        return tuple(self.price(context, contract, context_terms=terms) for contract in contracts)

    def _theoretical_price(
        self,
        option_type: OptionType,
        terms: BSContextTerms,
        strike_terms: BSStrikeTerms,
    ) -> Decimal:
        """Return undiscounted-per-unit theoretical price."""
        if option_type == OptionType.CALL:
            value = formulas.call_price(
                terms.spot,
                strike_terms.strike,
                terms.rate,
                terms.dividend_yield,
                terms.time_to_expiry,
                strike_terms.d1,
                strike_terms.d2,
            )
        else:
            value = formulas.put_price(
                terms.spot,
                strike_terms.strike,
                terms.rate,
                terms.dividend_yield,
                terms.time_to_expiry,
                strike_terms.d1,
                strike_terms.d2,
            )
        return to_decimal(max(value, 0.0))
