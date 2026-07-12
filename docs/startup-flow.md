# Startup Flow

```mermaid
sequenceDiagram
    participant Main
    participant Kernel as ApplicationKernel
    participant Config as ConfigurationManager
    participant Log as LoggingManager
    participant DI as Container
    participant Bus as EventBus
    participant Sched as SchedulerManager
    participant Plugins as PluginManager
    participant Repo as RepositoryFactory
    participant UI as QApplication

    Main->>Kernel: initialize()
    Kernel->>Config: load() / validate()
    Kernel->>Log: initialize()
    Kernel->>DI: resolve dependencies
    Kernel->>Bus: start()
    Kernel->>Repo: initialize()
    Kernel->>Sched: start()
    Kernel->>Plugins: discover_and_load()
    Main->>Kernel: start()
    Kernel->>UI: create_application()
    Kernel->>Bus: publish(ApplicationStarted)
    UI-->>Main: exec()
```

## Steps

1. **Load Config** — YAML files merged and validated via Pydantic
2. **Initialize Logger** — Loguru sinks configured
3. **Initialize DI** — Container resolves singletons
4. **Initialize Event Bus** — Background async worker started
5. **Initialize Scheduler** — APScheduler started
6. **Initialize Plugins** — Manifest discovery and load
7. **Initialize Workspace** — Workspace manager ready
8. **Initialize Repository Factory** — Data directories and placeholders
9. **Initialize UI** — Qt application instance created
10. **Run Application** — Qt event loop
