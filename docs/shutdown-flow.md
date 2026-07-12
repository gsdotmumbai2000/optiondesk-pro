# Shutdown Flow

```mermaid
sequenceDiagram
    participant Main
    participant Kernel as ApplicationKernel
    participant Bus as EventBus
    participant WS as WorkspaceManager
    participant Repo as RepositoryFactory
    participant Plugins as PluginManager
    participant Sched as SchedulerManager
    participant Log as LoggingManager

    Main->>Kernel: shutdown()
    Kernel->>Bus: publish(ApplicationShuttingDown)
    Kernel->>WS: save_active_profile()
    Kernel->>Repo: close()
    Kernel->>Plugins: unload_all()
    Kernel->>Sched: stop()
    Kernel->>Bus: publish(ApplicationStopped)
    Kernel->>Bus: stop()
    Kernel->>Log: shutdown()
```

## Steps

1. **Stop Workers** — Thread pool shutdown
2. **Save Workspace** — Active layout profile persisted
3. **Flush Logs** — Loguru complete()
4. **Close Repositories** — Repository factory cleanup
5. **Unload Plugins** — Plugin on_unload hooks
6. **Shutdown Scheduler** — APScheduler shutdown
7. **Close Application** — Exception handler uninstalled
