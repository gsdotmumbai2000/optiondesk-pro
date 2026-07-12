# OptionDesk Pro — Desktop UI Framework

Professional PySide6 MVVM desktop shell for OptionDesk Pro. The UI layer communicates **only** with the Application Services Layer through ViewModels. Business engines, brokers, and quantitative modules are never accessed directly from widgets.

## Architecture

```
View (PySide6 Widgets)
    ↓ bindings / commands
ViewModel (QObject + RelayCommand)
    ↓ ApplicationProvider
Application Services Layer
    ↓
Business Engines (frozen)
```

### Rules

- **MVVM**: Views bind to ViewModels; no business logic in widgets.
- **Commands**: User actions use `RelayCommand` on ViewModels.
- **Events**: `UIEventBridge` maps `EventBus` events to Qt signals.
- **Workers**: Heavy operations use `BackgroundWorker` (QThreadPool).
- **Themes**: `ThemeManager` applies QSS (light, dark, high contrast).

## Module Layout

| Path | Purpose |
|------|---------|
| `application/` | Qt app factory, `DesktopApplication`, worker pool |
| `main_window/` | Ribbon, menu, status bar, workspace tabs |
| `navigation/` | Left navigation pane |
| `docking/` | Dockable panels (monitor) |
| `workspaces/` | Workspace composition |
| `viewmodels/` | One ViewModel per workspace |
| `commands/` | `RelayCommand`, command IDs |
| `bindings/` | Signal binding helpers |
| `events/` | `UIEventBridge` |
| `themes/` | QSS themes |
| `charts/` | Chart placeholders |
| `option_chain/` | Option chain table (display only) |
| `dialogs/` | Open/Save dialogs |

## Quick Start

```python
from app.ui import DesktopApplication

app = DesktopApplication()
app.run()
```

Or integrate with the kernel (Qt app already created):

```python
from app.ui import DesktopApplication

desktop = DesktopApplication(event_bus=kernel.event_bus)
window = desktop.show()
```

## Workspaces

1. **Trading** — Strategy builder, evaluate/optimize, monitor panel
2. **Market** — Watchlist, indices, volatility, option chain
3. **Strategy** — Strategy list and open/save
4. **Portfolio** — Positions, PnL, margin, risk
5. **Backtesting** — Replay controls, trade log, performance
6. **AI** — Recommendations, explanations, confidence
7. **Reports** — Report list, export, history
8. **Settings** — Theme and preferences

## Diagrams

See `docs/ui/` for MVVM, navigation, workspace, and sequence diagrams.

## Qt Resources

Compile resources when adding icons:

```bash
pyside6-rcc src/app/ui/resources/resources.qrc -o src/app/ui/resources/resources_rc.py
```

## Performance

- UI updates target 60 FPS via signal-driven refresh.
- Long-running service calls run on `BackgroundWorker`.
- No calculations in the view layer.
