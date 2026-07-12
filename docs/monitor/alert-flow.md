# Alert Flow

## Rule to Alert Pipeline

```mermaid
flowchart TD
    R[AlertRule] --> E{TriggerEvaluator}
    E -->|threshold exceeded| T[AlertTrigger]
    E -->|within limits| X[No Action]
    T --> F[AlertFactory]
    F --> A[Alert]
    A --> AS[AlertService]
    AS --> C[MonitorCache]
    AS --> EB[AlertRaisedEvent]
    A --> REC[RecommendationEngine]
    REC --> RG[RecommendationGeneratedEvent]
```

## Built-in Rules

| Rule | Trigger | Engine Source |
|------|---------|---------------|
| Maximum Loss | Unrealized PnL ≤ threshold | PortfolioResult |
| Maximum Profit | Unrealized PnL ≥ threshold | PortfolioResult |
| Maximum Delta | \|delta\| ≥ threshold | RiskResult |
| Maximum Gamma | \|gamma\| ≥ threshold | RiskResult |
| Maximum Vega | \|vega\| ≥ threshold | RiskResult |
| Maximum Theta | theta ≤ threshold | RiskResult |
| Maximum Margin | utilization ≥ threshold | MarginResult |
| Maximum Drawdown | drawdown ≥ threshold | RiskResult / Performance |
| Time To Expiry | DTE ≤ threshold | CalculationContext |
| IV Spike | IV change ≥ threshold | RiskResult / Context |
| IV Crush | IV change ≤ threshold | CalculationContext |
| OI Shift | Option chain event | MarketDataEvent |
| Price Gap | Quote update event | MarketDataEvent |
| Custom | Expression flag | Configurable |

## Alert Priorities

| Priority | Use Case |
|----------|----------|
| Information | Profit target, IV crush |
| Warning | Greeks limits, expiry, price gap |
| Critical | Loss limit, margin, drawdown |
| Emergency | Reserved for future escalation |

## Acknowledgement Flow

```mermaid
sequenceDiagram
    participant User
    participant Service as PositionMonitorService
    participant Alerts as AlertService
    participant Cache as MonitorCache
    participant Bus as EventBus

    User->>Service: acknowledge_alert(request, alert_id)
    Service->>Alerts: acknowledge(alert_id)
    Alerts-->>Service: acknowledged Alert
    Service->>Cache: acknowledge(key, alert)
    Alerts->>Bus: AlertAcknowledgedEvent
    Service-->>User: acknowledged Alert
```

## Recommendation Mapping

| Trigger | Suggestion Type |
|---------|-----------------|
| Loss threshold | Reduce Risk |
| Profit target | Take Profit |
| Margin limit | Increase Capital |
| Delta limit | Hedge Position |
| Gamma limit | Reduce Position |
| Theta decay | Roll Position |
| Expiry warning | Close Position |
| Volatility spike | Reduce Position |
