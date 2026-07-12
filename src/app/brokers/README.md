# Broker Integration Layer

OptionDesk Pro uses a broker-agnostic integration layer. Application code depends only on `BrokerInterface`; Breeze is the first concrete implementation.

## Layout

```
src/app/brokers/
  broker_interface/   # BrokerInterface contract
  broker_factory/     # BrokerFactory
  broker_manager/     # lifecycle, reconnect, heartbeat
  breeze/             # Breeze adapter (only place Breeze SDK is used)
  zerodha/            # placeholder
  dhan/               # placeholder
  shared/             # domain models, enums, exceptions
```

## Usage

```python
from app.brokers.bootstrap import BrokerProvider
from app.config.models.app_config import BrokerConfig
from app.security.credential_manager import CredentialManager
from app.events.event_bus import EventBus

provider = BrokerProvider(BrokerConfig(), CredentialManager(), EventBus())
provider.manager.connect()
quote = provider.broker_service.get_quotes("NIFTY", "NFO")
provider.stop()
```

## Credentials

Store credentials via `CredentialManager` (never SQLite):

- `store_api_key(account_name, key)`
- `store_api_secret(account_name, secret)`
- `store_session_token(account_name, token)`

## Events

`BrokerConnected`, `BrokerDisconnected`, `SessionExpired`, `OrderPlaced`, `OrderModified`, `OrderCancelled`, `QuoteUpdated`, `OptionChainUpdated`, `PortfolioUpdated`

## Design Rules

- No Breeze types outside `brokers/breeze/`
- All responses normalized to `brokers/shared/models`
- Official Breeze API only via `breeze-connect` SDK
- Max 300 lines per file, dependency injection for testing
