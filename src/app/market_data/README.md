# Enterprise Market Data Engine

Single source of market data for OptionDesk Pro. All modules must obtain market information through this engine — never directly from the broker.

## Architecture

```
Broker (BrokerInterface)
        ↓ events / REST
MarketDataEngine
        ↓ normalize / validate
MarketCache (O(1) LRU + TTL)
        ↓ publish
EventBus + SubscriberRegistry
        ↓ persist
MarketDataRepository (market.db)
```

## Usage

```python
from app.market_data.bootstrap import MarketDataProvider
from pathlib import Path

provider = MarketDataProvider(broker, Path("./data"), event_bus)
provider.start()
quote = provider.engine.query.get_quote("NIFTY", "NFO")
provider.stop()
```

## Query API

- `get_quote`, `get_option_chain`, `get_historical`
- `get_latest`, `get_snapshot`, `get_atm_strike`
- `get_future`, `get_spot`, `get_oi`, `get_volume`

## Events

`QuoteUpdated`, `FutureUpdated`, `OptionChainUpdated`, `MarketOpened`, `MarketClosed`, `SnapshotUpdated`

## Workers

Quotes, Option Chain, Historical, Snapshot, Cache Cleanup — all run on background threads.
