# Black-Scholes Formula Documentation

## Model

Black-Scholes-Merton for European options with continuous dividend yield `q`.

### Inputs (from CalculationContext)

| Symbol | Source |
|--------|--------|
| S | `spot_price` |
| r | `risk_free_rate` |
| q | `dividend_yield` |
| σ | `volatility` |
| T | `time_to_expiry` (fractional year) |

Strike `K` comes from `OptionContract.strike`.

## Core Formulas

### Discount Factor

```
DF = exp(-rT)
```

### Forward Price

```
F = S * exp((r - q) * T)
```

### d1 and d2

```
d1 = [ln(S/K) + (r - q + σ²/2) * T] / (σ * sqrt(T))
d2 = d1 - σ * sqrt(T)
```

### European Call

```
C = S * exp(-qT) * N(d1) - K * exp(-rT) * N(d2)
```

### European Put

```
P = K * exp(-rT) * N(-d2) - S * exp(-qT) * N(-d1)
```

### Normal Distribution

```
φ(x) = (1 / sqrt(2π)) * exp(-x² / 2)        # PDF
N(x) = 0.5 * erfc(-x / sqrt(2))              # CDF
```

## Output Decomposition

```
Intrinsic = max(S - K, 0)   for calls
Intrinsic = max(K - S, 0)   for puts
Extrinsic = max(Theoretical - Intrinsic, 0)
```

Theoretical price in `PricingResult` is scaled by `OptionContract.multiplier`.

## Supported Instruments

- European index options (e.g. NIFTY, BANKNIFTY)
- European stock options

American exercise style is rejected at validation.

## Model Version

`ModelVersion.BLACK_SCHOLES_MERTON_V1` = `black-scholes-merton-v1`
