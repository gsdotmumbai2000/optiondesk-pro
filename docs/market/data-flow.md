# Market Master Data Flow

```mermaid
flowchart LR
    YAML[YAML/JSON Seeds] --> Repo[Repositories]
    Defaults[Built-in Defaults] --> Repo
    SQLite[(SQLite Cache)] --> Repo
    Repo --> Cache[MarketCache]
    Cache --> Services[Market Services]
    Services --> App[Other Modules]
    Cache --> Events[Event Bus]
```

## Load Order

1. Built-in underlying definitions
2. YAML/JSON seed files
3. SQLite persisted instruments

## Lazy Loading

`MarketCache` loads each subsystem on first access:

- Instruments
- Holidays
- Expiries
- Calendar/Sessions

Events are published when each layer is loaded.
