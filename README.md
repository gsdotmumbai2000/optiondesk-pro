# OptionDesk Pro

Professional Windows desktop options trading platform for Indian traders.

## Foundation Release (v0.1.0)

This release contains the **application framework only**:

- Application Kernel
- Configuration Manager (Pydantic v2)
- Dependency Injection (dependency-injector)
- Event Bus
- Service Registry
- Logging (Loguru)
- Plugin Framework
- Health Monitor
- Scheduler (APScheduler)
- Workspace Manager
- Credential Manager (Windows DPAPI)
- Global Exception Handling

**Not included in this release:** Breeze API, strategy engine, Greeks, database models, UI screens, charts.

## Requirements

- Python 3.13+
- Windows 10/11 (primary target)

## Setup

```bash
cd optiondesk-pro
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Run

```bash
optiondesk
```

Or:

```bash
python -m app.main
```

## Test

```bash
pytest
```

## Project Layout

```text
src/app/
  kernel/          Application lifecycle orchestration
  config/          Configuration manager and models
  core/            Service registry
  events/          Event bus and application events
  logging/         Loguru logging manager
  exceptions/      Exception hierarchy and global handler
  plugins/         Plugin loader and manager
  scheduler/       APScheduler wrapper
  security/        Credential manager (DPAPI)
  repositories/    Repository factory (placeholders)
  infrastructure/  DI container
  services/        Service keys (future business services)
  ui/              Minimal Qt application shell
  utils/           Shared utilities
  tests/           Pytest suite
```

## Architecture

See `docs/architecture-notes.md` for details.

## License

Proprietary.
