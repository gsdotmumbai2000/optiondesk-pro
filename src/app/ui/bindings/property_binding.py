"""Property binding helpers."""

from collections.abc import Callable

from PySide6.QtCore import QObject


def bind_signal(
    source: QObject,
    signal_name: str,
    handler: Callable[..., None],
) -> None:
    """Connect a signal to a handler by name."""
    signal = getattr(source, signal_name, None)
    if signal is not None:
        signal.connect(handler)


def bind_viewmodel_status(view, viewmodel) -> None:
    """Bind common viewmodel status signals to view slots."""
    if hasattr(view, "set_busy"):
        viewmodel.busy_changed.connect(view.set_busy)
    if hasattr(view, "show_status"):
        viewmodel.status_message_changed.connect(view.show_status)
    if hasattr(view, "show_error"):
        viewmodel.error_occurred.connect(view.show_error)
