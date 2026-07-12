"""Position monitor application service."""

from datetime import datetime, timezone

from app.events.event_bus import EventBus
from app.monitor.cache.monitor_cache import MonitorCache
from app.monitor.engine.monitor_engine import MonitorEngine
from app.monitor.events import MonitoringStartedEvent, MonitoringStoppedEvent
from app.monitor.exceptions import MonitorException
from app.monitor.models.enums import MonitoringInterval
from app.monitor.models.monitor import MonitoringSession, PositionMonitor
from app.monitor.models.request import MonitorAnalysisRequest
from app.monitor.models.result import MonitorResult
from app.monitor.providers.cache_keys import build_cache_key
from app.monitor.scheduler.monitoring_scheduler import MonitoringScheduler, ScheduleConfig
from app.monitor.services.alert_service import AlertService
from app.monitor.validation.monitor_validator import MonitorValidator
from app.utils.uuid_helper import generate_uuid


class PositionMonitorService:
    """Orchestrate monitoring, caching, and events."""

    def __init__(
        self,
        engine: MonitorEngine,
        validator: MonitorValidator | None = None,
        cache: MonitorCache | None = None,
        alert_service: AlertService | None = None,
        scheduler: MonitoringScheduler | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize service."""
        self._engine = engine
        self._validator = validator or MonitorValidator()
        self._cache = cache or MonitorCache()
        self._alerts = alert_service or AlertService(event_bus=event_bus)
        self._scheduler = scheduler or MonitoringScheduler()
        self._event_bus = event_bus
        self._sessions: dict[str, MonitoringSession] = {}

    @property
    def cache(self) -> MonitorCache:
        """Return monitor cache."""
        return self._cache

    def start_monitoring(
        self,
        portfolio_id: str,
        interval: MonitoringInterval = MonitoringInterval.EVERY_MINUTE,
        custom_seconds: int = 0,
    ) -> MonitoringSession:
        """Start monitoring session."""
        monitor = PositionMonitor(
            monitor_id=generate_uuid(),
            portfolio_id=portfolio_id,
            interval=interval,
            enabled=True,
            custom_interval_seconds=custom_seconds,
        )
        session = MonitoringSession(
            session_id=generate_uuid(),
            monitor_id=monitor.monitor_id,
            portfolio_id=portfolio_id,
            started_at=datetime.now(timezone.utc),
            interval=interval,
            is_active=True,
        )
        self._sessions[session.session_id] = session
        config = ScheduleConfig(interval=interval, custom_seconds=custom_seconds)
        self._scheduler.register(session.session_id, config, lambda: None)
        self._publish_started(session)
        return session

    def stop_monitoring(self, session_id: str) -> None:
        """Stop monitoring session."""
        self._scheduler.stop(session_id)
        session = self._sessions.get(session_id)
        if session is not None:
            self._sessions[session_id] = MonitoringSession(
                session_id=session.session_id,
                monitor_id=session.monitor_id,
                portfolio_id=session.portfolio_id,
                started_at=session.started_at,
                interval=session.interval,
                is_active=False,
                last_evaluated_at=session.last_evaluated_at,
            )
        self._publish_stopped(session_id)

    def evaluate(self, request: MonitorAnalysisRequest) -> MonitorResult:
        """Evaluate positions and cache result."""
        try:
            self._validator.validate_request(request)
            result = self._engine.evaluate(request)
            key = build_cache_key(request)
            self._cache.put(key, result)
            self._alerts.raise_alerts(result.open_alerts)
            return result
        except MonitorException:
            raise

    def get_latest(self, request: MonitorAnalysisRequest) -> MonitorResult | None:
        """Return latest cached result."""
        return self._cache.get_latest(build_cache_key(request))

    def refresh(self, request: MonitorAnalysisRequest) -> MonitorResult:
        """Invalidate and re-evaluate."""
        self._cache.invalidate(build_cache_key(request))
        return self.evaluate(request)

    def acknowledge_alert(self, request: MonitorAnalysisRequest, alert_id: str):
        """Acknowledge alert and update cache."""
        ack = self._alerts.acknowledge(alert_id)
        if ack is not None:
            self._cache.acknowledge(build_cache_key(request), ack)
        return ack

    def _publish_started(self, session: MonitoringSession) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            MonitoringStartedEvent(
                payload={"session_id": session.session_id}
            )
        )

    def _publish_stopped(self, session_id: str) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            MonitoringStoppedEvent(payload={"session_id": session_id})
        )
