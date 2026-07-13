"""Publish live analytics events."""

from app.events.event_bus import EventBus
from app.live.events import (
    GreeksUpdatedEvent,
    LiveAnalyticsRefreshedEvent,
    LiveOptionChainUpdatedEvent,
    MarginUpdatedEvent,
    OptionChainUpdatedEvent,
    PortfolioUpdatedEvent,
    PositionUpdatedEvent,
    ProbabilityUpdatedEvent,
    RiskCalculatedEvent,
    VolatilityUpdatedEvent,
)
from app.live.models.analytics import LiveAnalyticsSnapshot
from app.live.models.chain_key import ChainKey
from app.live.models.option_chain import LiveOptionChain


class AnalyticsPublisher:
    """Broadcast live analytics domain events."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._event_bus = event_bus

    def publish_chain(self, key: ChainKey, chain: LiveOptionChain) -> None:
        payload = {"chain_key": key.cache_key(), "chain": chain.model_dump(mode="json")}
        self._publish(LiveOptionChainUpdatedEvent(payload=payload))
        self._publish(OptionChainUpdatedEvent(payload=payload))

    def publish_snapshot(self, key: ChainKey, snapshot: LiveAnalyticsSnapshot) -> None:
        payload = {"chain_key": key.cache_key()}
        self._publish(LiveAnalyticsRefreshedEvent(payload=payload))
        if snapshot.greeks is not None:
            self._publish(GreeksUpdatedEvent(payload=payload))
        if snapshot.volatility is not None:
            self._publish(VolatilityUpdatedEvent(payload=payload))
        if snapshot.probability is not None:
            self._publish(ProbabilityUpdatedEvent(payload=payload))
        if snapshot.risk is not None:
            self._publish(RiskCalculatedEvent(payload=payload))
        if snapshot.margin is not None:
            self._publish(MarginUpdatedEvent(payload=payload))
        if snapshot.portfolio_greeks is not None:
            self._publish(PortfolioUpdatedEvent(payload=payload))
        if snapshot.position_greeks is not None:
            self._publish(PositionUpdatedEvent(payload=payload))

    def _publish(self, event: object) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)
