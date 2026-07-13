"""UI event bridge to application EventBus."""

from PySide6.QtCore import QObject, Signal

from app.application.events import (
    PortfolioLoadedEvent,
    RecommendationReadyEvent,
    StrategyLoadedEvent,
    WorkspaceOpenedEvent,
)
from app.brokers.events import (AuthenticationFailedEvent,
                                AuthenticationSucceededEvent,
                                BrokerConnectedEvent, BrokerDisconnectedEvent,
                                SessionExpiredEvent)
from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger
from app.market_data.diagnostics import market_data_debug_enabled
from app.market_data.events import (MarketClosedEvent, MarketOpenedEvent,
                                    QuoteUpdatedEvent, TickReceivedEvent)
from app.monitor.events import AlertRaisedEvent

logger = get_logger(__name__)


class UIEventBridge(QObject):
    """Bridge application events to Qt signals for ViewModels."""

    market_updated = Signal(dict)
    portfolio_updated = Signal(dict)
    strategy_updated = Signal(dict)
    alert_raised = Signal(dict)
    recommendation_ready = Signal(dict)
    workspace_opened = Signal(dict)
    broker_connected = Signal(dict)
    broker_disconnected = Signal(dict)
    session_expired = Signal(dict)
    authentication_succeeded = Signal(dict)
    authentication_failed = Signal(dict)
    tick_received = Signal(dict)
    market_opened = Signal(dict)
    market_closed = Signal(dict)

    def __init__(self, event_bus: EventBus | None, parent: QObject | None = None) -> None:
        """Initialize bridge."""
        super().__init__(parent)
        self._bus = event_bus
        if event_bus is not None:
            self._subscribe()

    def _subscribe(self) -> None:
        """Subscribe to application events."""
        assert self._bus is not None
        self._bus.subscribe(PortfolioLoadedEvent, self._on_portfolio)
        self._bus.subscribe(StrategyLoadedEvent, self._on_strategy)
        self._bus.subscribe(RecommendationReadyEvent, self._on_recommendation)
        self._bus.subscribe(AlertRaisedEvent, self._on_alert)
        self._bus.subscribe(WorkspaceOpenedEvent, self._on_workspace)
        self._bus.subscribe(BrokerConnectedEvent, self._on_broker_connected)
        self._bus.subscribe(BrokerDisconnectedEvent, self._on_broker_disconnected)
        self._bus.subscribe(SessionExpiredEvent, self._on_session_expired)
        self._bus.subscribe(AuthenticationSucceededEvent, self._on_auth_success)
        self._bus.subscribe(AuthenticationFailedEvent, self._on_auth_failed)
        self._bus.subscribe(TickReceivedEvent, self._on_tick)
        self._bus.subscribe(MarketOpenedEvent, self._on_market_opened)
        self._bus.subscribe(MarketClosedEvent, self._on_market_closed)
        self._bus.subscribe(QuoteUpdatedEvent, self._on_quote_updated)

    def _on_portfolio(self, event: PortfolioLoadedEvent) -> None:
        self.portfolio_updated.emit(event.payload)

    def _on_strategy(self, event: StrategyLoadedEvent) -> None:
        self.strategy_updated.emit(event.payload)

    def _on_recommendation(self, event: RecommendationReadyEvent) -> None:
        self.recommendation_ready.emit(event.payload)

    def _on_alert(self, event: AlertRaisedEvent) -> None:
        self.alert_raised.emit(event.payload)

    def _on_workspace(self, event: WorkspaceOpenedEvent) -> None:
        self.workspace_opened.emit(event.payload)

    def _on_broker_connected(self, event: BrokerConnectedEvent) -> None:
        self.broker_connected.emit(event.payload)

    def _on_broker_disconnected(self, event: BrokerDisconnectedEvent) -> None:
        self.broker_disconnected.emit(event.payload)

    def _on_session_expired(self, event: SessionExpiredEvent) -> None:
        self.session_expired.emit(event.payload)

    def _on_auth_success(self, event: AuthenticationSucceededEvent) -> None:
        self.authentication_succeeded.emit(event.payload)

    def _on_auth_failed(self, event: AuthenticationFailedEvent) -> None:
        self.authentication_failed.emit(event.payload)

    def _on_tick(self, event: TickReceivedEvent) -> None:
        tick = event.payload.get("tick", {})
        if market_data_debug_enabled():
            logger.info(
                "[UI-BRIDGE] UI EVENT BRIDGE "
                "symbol={symbol} ltp={ltp} timestamp={timestamp}",
                symbol=tick.get("symbol"),
                ltp=tick.get("ltp"),
                timestamp=tick.get("timestamp"),
            )
        self.tick_received.emit(event.payload)
        self.market_updated.emit(event.payload)

    def _on_market_opened(self, event: MarketOpenedEvent) -> None:
        self.market_opened.emit(event.payload)
        self.market_updated.emit(event.payload)

    def _on_market_closed(self, event: MarketClosedEvent) -> None:
        self.market_closed.emit(event.payload)
        self.market_updated.emit(event.payload)

    def _on_quote_updated(self, event: QuoteUpdatedEvent) -> None:
        self.market_updated.emit(event.payload)

    def emit_market_update(self, payload: dict) -> None:
        """Emit market update for UI refresh."""
        self.market_updated.emit(payload)
