# Quantitative Engine Integration Layer

The Quant module integrates all frozen quantitative engines into a single provider bundle.

## Scope

- Provider registry for pricing, Greeks, volatility, option chain, probability, payoff, risk, margin
- Strategy-compatible `EngineBundle` factory
- Event publication for initialization and bundle wiring

## Module Layout

```
src/app/quant/
  registry/       # QuantEngineRegistry
  providers/      # build_strategy_engine_bundle
  models/         # QuantEngineProviders
  services/       # QuantService
  bootstrap.py    # QuantProvider
```

## Quick Start

```python
from app.quant import QuantProvider

provider = QuantProvider(event_bus=event_bus)
bundle = provider.build_engine_bundle()
```
