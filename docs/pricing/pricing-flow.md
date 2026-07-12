# Black-Scholes Pricing Flow

## Single Contract

```mermaid
sequenceDiagram
    participant Client
    participant Service as PricingService
    participant Validator as PricingValidator
    participant Engine as BlackScholesEngine
    participant Terms as BSContextTerms

    Client->>Service: price(context, contract)
    Service->>Validator: validate(context, contract)
    Validator-->>Service: ok
    Service->>Engine: price(context, contract)
    Engine->>Terms: from_context(context)
    Terms-->>Engine: discount, forward, σ√T
    Engine->>Engine: build BSStrikeTerms(strike)
    Engine->>Engine: call_price / put_price
    Engine->>Engine: intrinsic + extrinsic
    Engine-->>Service: PricingResult
    Service-->>Client: PricingResult
```

## Batch Pricing

```mermaid
sequenceDiagram
    participant Client
    participant Service as PricingService
    participant Engine as BlackScholesEngine

    Client->>Service: price_many(context, contracts)
    Service->>Service: validate each contract
    Service->>Engine: price_many(context, contracts)
    Engine->>Engine: BSContextTerms.from_context once
    loop each contract
        Engine->>Engine: BSStrikeTerms + price
    end
    Engine-->>Service: tuple[PricingResult]
    Service-->>Client: results
```

## Validation Failure Paths

| Check | Exception |
|-------|-----------|
| T ≤ 0 | `ExpiredContractException` |
| Non-European style | `InvalidPricingInput` |
| Spot/strike/vol ≤ 0 | `InvalidPricingInput` |
| Expiry mismatch | `InvalidPricingInput` |

## Data Dependencies

```
CalculationContext ──► BSContextTerms ──► BSStrikeTerms ──► PricingResult
OptionContract     ────────────────────────┘
```

No broker, database, or market data engine access occurs inside the pricing module.

## Performance Path

1. Convert `Decimal` context fields to `float` once per context
2. Precompute `exp(-rT)`, forward price, and `σ√T`
3. Per strike: compute `d1`, `d2`, two CDF evaluations
4. Quantize outputs back to `Decimal` for result objects

Batch APIs avoid rebuilding step 1–2 for every strike.
