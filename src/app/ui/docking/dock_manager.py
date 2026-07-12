"""Dock panel manager."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QMainWindow

from app.ui.monitor.monitor_view import MonitorView
from app.ui.viewmodels.monitor_viewmodel import MonitorViewModel


class DockManager:
    """Configure dockable panels on main window."""

    def __init__(self, window: QMainWindow) -> None:
        self._window = window

    def add_monitor_dock(self, viewmodel: MonitorViewModel) -> QDockWidget:
        """Add position monitor dock panel."""
        dock = QDockWidget("Position Monitor", self._window)
        dock.setObjectName("monitorDock")
        dock.setWidget(MonitorView(viewmodel))
        self._window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        return dock
