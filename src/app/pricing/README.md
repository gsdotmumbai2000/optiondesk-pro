# Black-Scholes Pricing Engine

The Enterprise Black-Scholes Pricing Engine computes theoretical European option prices from immutable `CalculationContext` and `OptionContract` inputs.

## Scope

- European call and put pricing (index and stock options)
- Black-Scholes-Merton model with continuous dividend yield
- Input validation and structured `PricingResult` output

## Out of Scope

- Greeks, probability analytics, payoff, margin, strategy, portfolio

## Module Layout

```
src/app/pricing/
  black_scholes/    # formulas, distribution, engine, intermediates
  models/           # OptionContract, PricingResult, enums
  services/         # PricingService
  validation/       # PricingValidator
  exceptions/       # pricing errors
  utilities/        # intrinsic value, decimal helpers
  bootstrap.py      # PricingProvider wiring
```

## Quick Start

```python
from decimal import Decimal
from app.pricing import OptionContract, PricingProvider
from app.pricing.models.enums import OptionType

provider = PricingProvider()
contract = OptionContract(
    strike=Decimal("24000"),
    option_type=OptionType.CALL,
    expiry=context.expiry,
    multiplier=context.lot_size,
)
result = provider.service.price(context, contract)
print(result.theoretical_price, result.d1, result.d2)
```

## Batch Pricing

```python
results = provider.service.price_many(context, (call_contract, put_contract))
```

`price_many` reuses strike-independent intermediates (`BSContextTerms`) for throughput.

## Documentation

- [Formula Documentation](../../docs/pricing/formulas.md)
- [Class Diagram](../../docs/pricing/class-diagram.md)
- [Pricing Flow](../../docs/pricing/pricing-flow.md)

## Performance

Target: 100,000 pricing calculations per second via:

- Float kernels with `math.erfc` for CDF
- Reused `BSContextTerms` in batch pricing
- Precomputed discount factor, forward price, and `σ√T`
