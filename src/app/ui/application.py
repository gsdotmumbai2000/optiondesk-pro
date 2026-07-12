"""Minimal Qt application shell.

Full UI screens and charts will be implemented in future phases.
"""

from typing import cast

from PySide6.QtWidgets import QApplication

from app.utils.constants import APP_NAME


def create_application() -> QApplication:
    """Create the Qt application instance."""
    app = QApplication.instance()
    if app is not None:
        return cast(QApplication, app)
    qt_app = QApplication([])
    qt_app.setApplicationName(APP_NAME)
    qt_app.setOrganizationName("OptionDesk")
    return qt_app
