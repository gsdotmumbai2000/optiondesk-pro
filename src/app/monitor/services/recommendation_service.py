"""Recommendation application service."""

from app.events.event_bus import EventBus
from app.monitor.events import RecommendationGeneratedEvent
from app.monitor.models.recommendation import Recommendation
from app.monitor.models.request import MonitorAnalysisRequest
from app.monitor.recommendations.engine import RecommendationEngine


class RecommendationService:
    """Expose recommendation generation."""

    def __init__(
        self,
        engine: RecommendationEngine | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize service."""
        self._engine = engine or RecommendationEngine()
        self._event_bus = event_bus

    def generate(
        self,
        request: MonitorAnalysisRequest,
        alerts,
    ) -> tuple[Recommendation, ...]:
        """Generate recommendations and publish event."""
        recs = self._engine.generate(request, alerts)
        if recs and self._event_bus is not None:
            self._event_bus.publish(
                RecommendationGeneratedEvent(
                    payload={"count": str(len(recs))}
                )
            )
        return recs
