"""Monitor engine bootstrap."""

from app.events.event_bus import EventBus
from app.monitor.cache.monitor_cache import MonitorCache
from app.monitor.engine.monitor_engine import MonitorEngine
from app.monitor.scheduler.monitoring_scheduler import MonitoringScheduler
from app.monitor.services.alert_service import AlertService
from app.monitor.services.notification_service import NotificationService
from app.monitor.services.position_monitor_service import PositionMonitorService
from app.monitor.services.recommendation_service import RecommendationService
from app.monitor.services.rule_engine import RuleEngine
from app.monitor.validation.monitor_validator import MonitorValidator


class MonitorProvider:
    """Wire monitor engine dependencies."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize provider."""
        self.engine = MonitorEngine()
        self.validator = MonitorValidator()
        self.cache = MonitorCache()
        self.scheduler = MonitoringScheduler()
        self.rule_engine = RuleEngine(validator=self.validator)
        self.notification_service = NotificationService()
        self.alert_service = AlertService(
            event_bus=event_bus, notification_service=self.notification_service,
        )
        self.recommendation_service = RecommendationService(event_bus=event_bus)
        self.service = PositionMonitorService(
            self.engine,
            self.validator,
            self.cache,
            self.alert_service,
            self.scheduler,
            event_bus,
        )
