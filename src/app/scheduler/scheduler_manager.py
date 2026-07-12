"""Scheduler management using APScheduler."""

from collections.abc import Callable
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.logging.logging_manager import get_logger

logger = get_logger(__name__)
JobCallable = Callable[[], None]


class SchedulerManager:
    """Manage scheduled background jobs."""

    def __init__(self, timezone: str = "Asia/Kolkata") -> None:
        """Initialize the scheduler manager."""
        self._scheduler = BackgroundScheduler(timezone=timezone)
        self._timezone = timezone

    @property
    def is_running(self) -> bool:
        """Return whether the scheduler is running."""
        return bool(self._scheduler.running)

    def start(self) -> None:
        """Start the scheduler."""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")

    def pause(self) -> None:
        """Pause the scheduler."""
        self._scheduler.pause()
        logger.info("Scheduler paused")

    def resume(self) -> None:
        """Resume the scheduler."""
        self._scheduler.resume()
        logger.info("Scheduler resumed")

    def add_interval_job(
        self,
        job_id: str,
        func: JobCallable,
        *,
        seconds: int,
        enabled: bool = True,
    ) -> None:
        """Add an interval job."""
        if not enabled:
            return
        self._scheduler.add_job(
            func,
            trigger=IntervalTrigger(seconds=seconds, timezone=self._timezone),
            id=job_id,
            replace_existing=True,
        )

    def add_cron_job(
        self,
        job_id: str,
        func: JobCallable,
        *,
        cron_expression: str,
        enabled: bool = True,
    ) -> None:
        """Add a cron job."""
        if not enabled:
            return
        trigger = self._parse_cron(cron_expression)
        self._scheduler.add_job(func, trigger=trigger, id=job_id, replace_existing=True)

    def add_one_time_job(
        self, job_id: str, func: JobCallable, *, run_date: Any
    ) -> None:
        """Add a one-time job."""
        self._scheduler.add_job(
            func,
            trigger=DateTrigger(run_date=run_date, timezone=self._timezone),
            id=job_id,
            replace_existing=True,
        )

    def remove_job(self, job_id: str) -> None:
        """Remove a scheduled job."""
        self._scheduler.remove_job(job_id)

    def enable_job(self, job_id: str) -> None:
        """Resume a paused job."""
        self._scheduler.resume_job(job_id)

    def disable_job(self, job_id: str) -> None:
        """Pause a scheduled job."""
        self._scheduler.pause_job(job_id)

    def _parse_cron(self, expression: str) -> CronTrigger:
        """Parse a simple 5-field cron expression."""
        parts = expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expression}")
        minute, hour, day, month, day_of_week = parts
        return CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            timezone=self._timezone,
        )
