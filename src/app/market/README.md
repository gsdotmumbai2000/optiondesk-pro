# Market Master Module

The Market Master subsystem is the single source of truth for all tradable instrument metadata in OptionDesk Pro.

## Responsibilities

- Instrument and underlying master data
- Exchange definitions
- Expiry rules and calendars
- Trading holidays and special sessions
- Trading session windows
- Market calendar queries
- Strike and DTE/TTE utilities

## Usage

```python
from pathlib import Path
from app.market.bootstrap import MarketMasterProvider

provider = MarketMasterProvider(Path("./data"))
nifty = provider.instrument_service.find_by_symbol("NIFTY")
lot_size = provider.instrument_service.get_lot_size("NIFTY")
expiry = provider.expiry_service.nearest_expiry(
    "NIFTY",
    "NSEFO",
    on_date=date.today(),
)
provider.shutdown()
```

## Data Sources

1. Built-in defaults for NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY, SENSEX
2. YAML/JSON seed files in `resources/market/`
3. SQLite cache in `config.db` table `market_instruments`

## Architecture

See `docs/market/` for diagrams and data flow.
