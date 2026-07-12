"""Health monitor."""

import shutil
from dataclasses import asdict, dataclass, field
from enum import Enum

import psutil

from app.events.application_events import HealthStatusChangedEvent
from app.events.event_bus import EventBus
from app.logging.logging_manager import get_logger
from app.plugins.plugin_registry import PluginRegistry
from app.repositories.repository_factory import RepositoryFactory
from app.scheduler.scheduler_manager import SchedulerManager

logger = get_logger(__name__)


class HealthLevel(str, Enum):
    """Health severity levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


@dataclass
class HealthProbe:
    """Single health probe result."""

    name: str
    level: HealthLevel
    message: str
    value: str = ""


@dataclass
class HealthSnapshot:
    """Aggregated health status."""

    overall: HealthLevel = HealthLevel.HEALTHY
    probes: list[HealthProbe] = field(default_factory=list)


class HealthMonitor:
    """Monitor subsystem health and publish status updates."""

    def __init__(
        self,
        event_bus: EventBus,
        repository_factory: RepositoryFactory,
        scheduler_manager: SchedulerManager,
        plugin_registry: PluginRegistry,
    ) -> None:
        """Initialize the health monitor."""
        self._event_bus = event_bus
        self._repository_factory = repository_factory
        self._scheduler_manager = scheduler_manager
        self._plugin_registry = plugin_registry
        self._broker_connected = False
        self._worker_count = 0
        self._running = False
        self._last_snapshot = HealthSnapshot()

    @property
    def snapshot(self) -> HealthSnapshot:
        """Return the latest health snapshot."""
        return self._last_snapshot

    def set_broker_connected(self, connected: bool) -> None:
        """Update broker connection status."""
        self._broker_connected = connected

    def set_worker_count(self, count: int) -> None:
        """Update active worker count."""
        self._worker_count = count

    def start(self) -> None:
        """Start health monitoring."""
        self._running = True
        self.refresh()
        logger.info("Health monitor started")

    def stop(self) -> None:
        """Stop health monitoring."""
        self._running = False
        logger.info("Health monitor stopped")

    def refresh(self) -> HealthSnapshot:
        """Refresh and publish health status."""
        probes = [
            self._probe_cpu(),
            self._probe_memory(),
            self._probe_disk(),
            self._probe_database(),
            self._probe_broker(),
            self._probe_workers(),
            self._probe_scheduler(),
            self._probe_plugins(),
        ]
        overall = self._aggregate(probes)
        snapshot = HealthSnapshot(overall=overall, probes=probes)
        self._last_snapshot = snapshot
        self._event_bus.publish(
            HealthStatusChangedEvent(
                payload={
                    "overall": overall.value,
                    "probes": [asdict(probe) for probe in probes],
                }
            )
        )
        return snapshot

    def _aggregate(self, probes: list[HealthProbe]) -> HealthLevel:
        """Aggregate probe results."""
        if any(probe.level == HealthLevel.CRITICAL for probe in probes):
            return HealthLevel.CRITICAL
        if any(probe.level == HealthLevel.DEGRADED for probe in probes):
            return HealthLevel.DEGRADED
        return HealthLevel.HEALTHY

    def _probe_cpu(self) -> HealthProbe:
        """Probe CPU usage."""
        value = f"{psutil.cpu_percent(interval=0.1):.1f}%"
        return HealthProbe(
            name="cpu", level=HealthLevel.HEALTHY, message="CPU OK", value=value
        )

    def _probe_memory(self) -> HealthProbe:
        """Probe memory usage."""
        process = psutil.Process()
        rss_mb = process.memory_info().rss / (1024 * 1024)
        level = HealthLevel.DEGRADED if rss_mb > 1024 else HealthLevel.HEALTHY
        return HealthProbe(
            name="memory",
            level=level,
            message="Memory usage monitored",
            value=f"{rss_mb:.1f} MB",
        )

    def _probe_disk(self) -> HealthProbe:
        """Probe disk usage."""
        usage = shutil.disk_usage(self._repository_factory.data_directory)
        free_gb = usage.free / (1024**3)
        level = HealthLevel.DEGRADED if free_gb < 1 else HealthLevel.HEALTHY
        return HealthProbe(
            name="disk",
            level=level,
            message="Disk space monitored",
            value=f"{free_gb:.1f} GB free",
        )

    def _probe_database(self) -> HealthProbe:
        """Probe database availability."""
        data_dir = self._repository_factory.data_directory
        level = HealthLevel.HEALTHY if data_dir.exists() else HealthLevel.CRITICAL
        message = (
            "Database directory available"
            if data_dir.exists()
            else "Database directory missing"
        )
        return HealthProbe(
            name="database", level=level, message=message, value=str(data_dir)
        )

    def _probe_broker(self) -> HealthProbe:
        """Probe broker connectivity."""
        level = HealthLevel.HEALTHY if self._broker_connected else HealthLevel.DEGRADED
        message = (
            "Broker connected" if self._broker_connected else "Broker disconnected"
        )
        return HealthProbe(name="broker", level=level, message=message)

    def _probe_workers(self) -> HealthProbe:
        """Probe worker thread status."""
        level = (
            HealthLevel.DEGRADED if self._worker_count > 100 else HealthLevel.HEALTHY
        )
        return HealthProbe(
            name="workers",
            level=level,
            message="Worker queue monitored",
            value=str(self._worker_count),
        )

    def _probe_scheduler(self) -> HealthProbe:
        """Probe scheduler status."""
        running = self._scheduler_manager.is_running
        level = HealthLevel.HEALTHY if running else HealthLevel.DEGRADED
        message = "Scheduler running" if running else "Scheduler stopped"
        return HealthProbe(name="scheduler", level=level, message=message)

    def _probe_plugins(self) -> HealthProbe:
        """Probe plugin health."""
        plugins = self._plugin_registry.list_plugins()
        return HealthProbe(
            name="plugins",
            level=HealthLevel.HEALTHY,
            message="Plugins monitored",
            value=str(len(plugins)),
        )
