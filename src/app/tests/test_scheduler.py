"""Scheduler manager tests."""

from datetime import datetime, timedelta

from app.scheduler.scheduler_manager import SchedulerManager


def test_scheduler_start_and_stop() -> None:
    """Scheduler should start and stop cleanly."""
    scheduler = SchedulerManager()
    scheduler.start()
    assert scheduler.is_running is True
    scheduler.stop()
    assert scheduler.is_running is False


def test_scheduler_interval_job_runs() -> None:
    """Interval jobs should be accepted by the scheduler."""
    scheduler = SchedulerManager()
    scheduler.start()
    scheduler.add_interval_job("heartbeat", lambda: None, seconds=60)
    scheduler.pause()
    scheduler.resume()
    scheduler.disable_job("heartbeat")
    scheduler.enable_job("heartbeat")
    scheduler.remove_job("heartbeat")
    scheduler.stop()


def test_scheduler_one_time_job() -> None:
    """One-time jobs should be schedulable."""
    scheduler = SchedulerManager()
    scheduler.start()
    run_at = datetime.now() + timedelta(seconds=30)
    scheduler.add_one_time_job("once", lambda: None, run_date=run_at)
    scheduler.stop()
