"""Theme manager."""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory

from app.ui.models.ui_enums import UITheme


def _palette(colors: dict[QPalette.ColorRole, str]) -> QPalette:
    """Build a QPalette from role->hex-color pairs, applied to All/Active
    and disabled Text/WindowText/ButtonText roles dimmed so disabled widgets
    stay legible instead of using the enabled color at full brightness."""
    palette = QPalette()
    for role, hex_color in colors.items():
        palette.setColor(QPalette.ColorGroup.All, role, QColor(hex_color))
    disabled_text = QColor(colors.get(QPalette.ColorRole.WindowText, "#808080"))
    disabled_text.setAlpha(120)
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText, QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, disabled_text)
    return palette


_DARK_COLORS = {
    QPalette.ColorRole.Window: "#0d1117",
    QPalette.ColorRole.WindowText: "#e6edf3",
    QPalette.ColorRole.Base: "#0d1117",
    QPalette.ColorRole.AlternateBase: "#161b22",
    QPalette.ColorRole.ToolTipBase: "#161b22",
    QPalette.ColorRole.ToolTipText: "#e6edf3",
    QPalette.ColorRole.Text: "#e6edf3",
    QPalette.ColorRole.PlaceholderText: "#8b949e",
    QPalette.ColorRole.Button: "#21262d",
    QPalette.ColorRole.ButtonText: "#e6edf3",
    QPalette.ColorRole.BrightText: "#f85149",
    QPalette.ColorRole.Link: "#1f6feb",
    QPalette.ColorRole.Highlight: "#1f6feb",
    QPalette.ColorRole.HighlightedText: "#ffffff",
}

_HIGH_CONTRAST_COLORS = {
    QPalette.ColorRole.Window: "#000000",
    QPalette.ColorRole.WindowText: "#ffffff",
    QPalette.ColorRole.Base: "#000000",
    QPalette.ColorRole.AlternateBase: "#000000",
    QPalette.ColorRole.ToolTipBase: "#000000",
    QPalette.ColorRole.ToolTipText: "#ffffff",
    QPalette.ColorRole.Text: "#ffffff",
    QPalette.ColorRole.PlaceholderText: "#ffffff",
    QPalette.ColorRole.Button: "#000000",
    QPalette.ColorRole.ButtonText: "#ffffff",
    QPalette.ColorRole.BrightText: "#ffff00",
    QPalette.ColorRole.Link: "#ffff00",
    QPalette.ColorRole.Highlight: "#ffff00",
    QPalette.ColorRole.HighlightedText: "#000000",
}


class ThemeManager:
    """Switch between light (native Windows look), dark, and high-contrast
    themes via QPalette + the Fusion style, not per-widget QSS color rules.

    QSS text/background colors have to be repeated per widget class (QLabel,
    QDialog, QMenu, QComboBox popup, ...) and it's easy to miss one -- every
    miss is an invisible-text bug. A QPalette is what every native widget
    (including QMenu/submenus and QDialog, which previously fell through
    every color rule this app declared) actually paints itself from, so
    setting it once covers all of them by construction. Fusion is the style
    that reliably honors a custom QPalette across menus/comboboxes/dialogs;
    Windows' own native style mostly ignores QPalette for chrome and has no
    real dark-mode menu rendering pre-Windows 11, which is why a Qt QSS/
    palette theme -- not the OS's own theme -- is what "dark mode" means
    here.
    """

    def __init__(self) -> None:
        """Initialize theme manager."""
        self._current = UITheme.DARK
        self._native_style_name: str | None = None
        self._native_palette: QPalette | None = None

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
        self._capture_native_defaults(app)
        app.setStyleSheet("")
        if theme == UITheme.LIGHT:
            app.setStyle(QStyleFactory.create(self._native_style_name))
            app.setPalette(self._native_palette)
        elif theme == UITheme.HIGH_CONTRAST:
            app.setStyle(QStyleFactory.create("Fusion"))
            app.setPalette(_palette(_HIGH_CONTRAST_COLORS))
        else:
            app.setStyle(QStyleFactory.create("Fusion"))
            app.setPalette(_palette(_DARK_COLORS))

    def _capture_native_defaults(self, app: QApplication) -> None:
        """Remember the OS-native style/palette the first time apply() runs,
        so switching back to LIGHT restores Windows' own look rather than a
        Fusion approximation of it."""
        if self._native_style_name is None:
            self._native_style_name = app.style().objectName()
            self._native_palette = QPalette(app.palette())

    def cycle(self) -> UITheme:
        """Cycle to next theme."""
        order = [UITheme.LIGHT, UITheme.DARK, UITheme.HIGH_CONTRAST]
        idx = order.index(self._current)
        nxt = order[(idx + 1) % len(order)]
        self.apply(nxt)
        return nxt
