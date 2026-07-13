# Subscription Lifecycle

## Operations

| Operation | API | Behavior |
|-----------|-----|----------|
| Subscribe | `MarketDataService.subscribe()` | Queue symbol; broker call if connected |
| Unsubscribe | `MarketDataService.unsubscribe()` | Remove from pending and active |
| Bulk Subscribe | `MarketDataService.bulk_subscribe()` | Multiple symbols in one call |
| Bulk Unsubscribe | `MarketDataService.bulk_unsubscribe()` | Remove multiple symbols |
| Resubscribe | `SubscriptionService.resubscribe_all()` | Re-send active subs after reconnect |

## Pending vs Active

```text
register / subscribe
        │
        ▼
   [_pending map]  ◄── watchlist (always retained on disconnect)
        │
        │ can_subscribe() == True
        ▼
   [_active map]   ◄── broker QuoteSubscription sent
        │
        │ deactivate_all() on disconnect
        ▼
   [_active cleared, _pending kept]
```

## Supported Instruments

Subscriptions support all Breeze product types via `ProductType`:

- Spot / Index (`CASH`)
- Options (`OPTIONS`)
- Futures (`FUTURES`)
- Currency
- Commodity

Option and future subscriptions include `expiry_date`, `strike_price`, and `option_right` where applicable.

## Default Indices

On engine start, these symbols are registered as **pending**:

- NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY (NSE CASH)

They activate automatically when the broker session becomes valid.

## Events

| Event | Payload |
|-------|---------|
| `SubscriptionAddedEvent` | symbol, exchange, product_type |
| `SubscriptionRemovedEvent` | symbol, exchange, product_type |

## Validation

`SubscriptionValidator` rejects empty symbol or exchange before queueing.

## Application Integration

Workspace services obtain prices only through `MarketDataService`:

- `MarketWorkspaceService` — watchlist, quotes, status
- `StrategyWorkspaceService.underlying_price()`
- `PortfolioWorkspaceService.position_market_price()`, `monitor_live_prices()`
- `TradingWorkspaceService.live_quote()`
- `AIWorkspaceService.market_context_price()`

No UI changes are required; ViewModels should call workspace service methods that delegate to `MarketDataService`.
