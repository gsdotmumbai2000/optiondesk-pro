# Replay Flow

```mermaid
flowchart TD
    A[HistoricalMarketData] --> B[ReplayEngine]
    C[HistoricalOptionChainData] --> B
    B --> D[start]
    D --> E{state?}
    E -->|RUNNING| F[step_forward]
    F --> G[ReplayEvent]
    G --> H[bar + chain snapshot]
    H --> I{more bars?}
    I -->|Yes| F
    I -->|No| J[FINISHED]
    E -->|PAUSED| K[pause]
    K --> L[resume]
    L --> E
```

## Controls

| Control | Description |
|---------|-------------|
| `start` | Begin replay from index |
| `pause` / `resume` | Pause and resume session |
| `step_forward` | Advance by step_size × speed |
| `fast_forward` | Jump to bar index |
| `set_speed` | 1x, 2x, 5x, 10x, MAX |

## Events

- `ReplayStartedEvent` — session begins
- `ReplayPausedEvent` — session paused
- `ReplayFinishedEvent` — all bars consumed
