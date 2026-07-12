"""Event bus tests."""

from app.events.application_events import ApplicationStartedEvent
from app.events.event_bus import EventBus


def test_event_bus_sync_subscribe_and_publish() -> None:
    """Synchronous handlers should receive published events."""
    bus = EventBus()
    received: list[str] = []

    bus.subscribe(
        ApplicationStartedEvent, lambda event: received.append(event.event_id)
    )
    bus.publish(ApplicationStartedEvent(payload={"test": True}))
    assert len(received) == 1


def test_event_bus_unsubscribe() -> None:
    """Unsubscribed handlers should not receive events."""
    bus = EventBus()
    received: list[str] = []

    def handler(event: ApplicationStartedEvent) -> None:
        received.append(event.event_id)

    bus.subscribe(ApplicationStartedEvent, handler)
    bus.unsubscribe(ApplicationStartedEvent, handler)  # type: ignore[arg-type]
    bus.publish(ApplicationStartedEvent())
    assert len(received) == 0


def test_event_bus_async_delivery() -> None:
    """Async delivery should process queued events."""
    import time

    bus = EventBus()
    bus.start()
    received: list[str] = []

    def handler(event: ApplicationStartedEvent) -> None:
        received.append(event.event_id)

    bus.subscribe(ApplicationStartedEvent, handler, async_handler=True)
    bus.publish_async(ApplicationStartedEvent())
    time.sleep(0.3)
    bus.stop()
    assert len(received) == 1
