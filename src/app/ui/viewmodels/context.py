"""ViewModel factory context."""

from dataclasses import dataclass

from app.application.bootstrap import ApplicationProvider
from app.ui.application.worker_pool import BackgroundWorker
from app.ui.events.ui_event_bridge import UIEventBridge


@dataclass(frozen=True, slots=True)
class ViewModelContext:
    """Shared dependencies for ViewModels."""

    provider: ApplicationProvider
    worker: BackgroundWorker
    events: UIEventBridge
    session_id: str
