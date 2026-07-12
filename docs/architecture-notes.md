# Architecture Notes

## Overview

OptionDesk Pro follows **Clean Architecture** and **Hexagonal Architecture** principles aligned with the frozen architecture specification (v2.1).

## Layers

| Layer | Package | Responsibility |
|-------|---------|----------------|
| Kernel | `app.kernel` | Application lifecycle, startup, shutdown |
| Configuration | `app.config` | Typed configuration loading and persistence |
| Core | `app.core` | Service registry and lifecycle |
| Events | `app.events` | Pub/sub event bus |
| Infrastructure | `app.infrastructure` | Dependency injection container |
| Repositories | `app.repositories` | Repository factory (persistence adapters in future phases) |
| Plugins | `app.plugins` | Plugin discovery and lifecycle |
| Security | `app.security` | Credential storage via Windows DPAPI |
| UI | `app.ui` | Minimal Qt shell (screens in future phases) |

## Dependency Rules

- UI must not access SQLite or Breeze directly
- Business services resolve through `ServiceRegistry`
- Configuration is loaded before logging and DI wiring
- Kernel is the only module that initializes the application

## Startup Order

1. Load configuration
2. Initialize logging
3. Initialize dependency injection
4. Initialize event bus
5. Initialize scheduler
6. Initialize plugins
7. Initialize workspace manager
8. Initialize repository factory
9. Initialize UI
10. Run Qt event loop

## Shutdown Order

1. Stop workers
2. Save workspace
3. Flush logs
4. Close repositories
5. Unload plugins
6. Shutdown scheduler
7. Close application

## Future Integration Points

| Component | Service Key | Status |
|-----------|-------------|--------|
| Market Data Service | `market_data_service` | Planned |
| Strategy Service | `strategy_service` | Planned |
| Portfolio Service | `portfolio_service` | Planned |
| Calculation Engine | `calculation_engine` | Planned |
| Breeze Adapter | `broker_service` | Planned |
