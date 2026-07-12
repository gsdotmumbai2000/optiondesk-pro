"""Theme manager."""

from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.ui.models.ui_enums import UITheme

THEMES_DIR = Path(__file__).resolve().parent


class ThemeManager:
    """Apply Qt stylesheets for light, dark, and high contrast themes."""

    def __init__(self) -> None:
        """Initialize theme manager."""
        self._current = UITheme.DARK

    @property
    def current_theme(self) -> UITheme:
        """Return active theme."""
        return self._current

    def apply(self, theme: UITheme) -> None:
        """Apply theme to QApplication."""
        self._current = theme
        app = QApplication.instance()
        if app is None:
            return
        qss_path = THEMES_DIR / f"{theme.value}.qss"
        if qss_path.exists():
            app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
        else:
            app.setStyleSheet("")

    def cycle(self) -> UITheme:
        """Cycle to next theme."""
        order = [UITheme.LIGHT, UITheme.DARK, UITheme.HIGH_CONTRAST]
        idx = order.index(self._current)
        nxt = order[(idx + 1) % len(order)]
        self.apply(nxt)
        return nxt
