"""Event bus implementation."""

import threading
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue
from typing import TypeVar

from app.events.application_events import ApplicationEvent
from app.logging.logging_manager import get_logger

TEvent = TypeVar("TEvent", bound=ApplicationEvent)
EventHandler = Callable[[ApplicationEvent], None]

logger = get_logger(__name__)


class EventBus:
    """Thread-safe publish/subscribe event bus."""

    def __init__(self, async_workers: int = 2) -> None:
        """Initialize the event bus."""
        self._sync_handlers: dict[type[ApplicationEvent], list[EventHandler]] = (
            defaultdict(list)
        )
        self._async_handlers: dict[type[ApplicationEvent], list[EventHandler]] = (
            defaultdict(list)
        )
        self._wildcard_handlers: list[EventHandler] = []
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=async_workers)
        self._async_queue: Queue[ApplicationEvent] = Queue()
        self._running = False
        self._worker_thread: threading.Thread | None = None

    def start(self) -> None:
        """Start asynchronous event processing."""
        if self._running:
            return
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._process_async_queue,
            name="event-bus-worker",
            daemon=True,
        )
        self._worker_thread.start()
        logger.info("Event bus started")

    def stop(self) -> None:
        """Stop asynchronous event processing."""
        self._running = False
        if self._worker_thread is not None:
            self._worker_thread.join(timeout=5)
            self._worker_thread = None
        self._executor.shutdown(wait=True, cancel_futures=False)
        logger.info("Event bus stopped")

    def subscribe(
        self,
        event_type: type[TEvent],
        handler: Callable[[TEvent], None],
        *,
        async_handler: bool = False,
    ) -> None:
        """Subscribe to an event type."""
        typed_handler: EventHandler = handler  # type: ignore[assignment]
        with self._lock:
            bucket = self._async_handlers if async_handler else self._sync_handlers
            if typed_handler not in bucket[event_type]:
                bucket[event_type].append(typed_handler)

    def subscribe_all(
        self, handler: EventHandler, *, async_handler: bool = False
    ) -> None:
        """Subscribe to all events."""
        with self._lock:
            if async_handler:
                if handler not in self._async_handlers[ApplicationEvent]:
                    self._async_handlers[ApplicationEvent].append(handler)
            elif handler not in self._wildcard_handlers:
                self._wildcard_handlers.append(handler)

    def unsubscribe(self, event_type: type[TEvent], handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type."""
        with self._lock:
            for bucket in (self._sync_handlers, self._async_handlers):
                if handler in bucket.get(event_type, []):
                    bucket[event_type].remove(handler)

    def publish(self, event: ApplicationEvent, *, async_delivery: bool = False) -> None:
        """Publish an event to subscribers."""
        if async_delivery:
            self._async_queue.put(event)
            return
        self._dispatch_sync(event)

    def publish_async(self, event: ApplicationEvent) -> None:
        """Publish an event asynchronously."""
        self.publish(event, async_delivery=True)

    def _process_async_queue(self) -> None:
        """Background worker for async queue delivery."""
        while self._running:
            try:
                event = self._async_queue.get(timeout=0.25)
            except Empty:
                continue
            self._dispatch_async(event)

    def _dispatch_sync(self, event: ApplicationEvent) -> None:
        """Dispatch event to synchronous handlers."""
        handlers = self._collect_handlers(event, async_only=False)
        for handler in handlers:
            self._safe_invoke(handler, event)

    def _dispatch_async(self, event: ApplicationEvent) -> None:
        """Dispatch event to asynchronous handlers."""
        handlers = self._collect_handlers(event, async_only=True)
        for handler in handlers:
            self._executor.submit(self._safe_invoke, handler, event)

    def _collect_handlers(
        self,
        event: ApplicationEvent,
        *,
        async_only: bool,
    ) -> list[EventHandler]:
        """Collect handlers for an event."""
        event_type = type(event)
        with self._lock:
            if async_only:
                handlers = list(self._async_handlers.get(event_type, []))
                handlers.extend(self._async_handlers.get(ApplicationEvent, []))
                return handlers

            handlers = list(self._sync_handlers.get(event_type, []))
            handlers.extend(self._sync_handlers.get(ApplicationEvent, []))
            handlers.extend(self._wildcard_handlers)
            return handlers

    @staticmethod
    def _safe_invoke(handler: EventHandler, event: ApplicationEvent) -> None:
        """Invoke a handler without propagating exceptions."""
        try:
            handler(event)
        except Exception as error:
            logger.exception("Event handler failed: {error}", error=error)
