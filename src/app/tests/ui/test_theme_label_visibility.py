"""Regression tests for theme text visibility.

Two real, user-reported bugs drove this: (1) an unstyled QLabel rendered
with near-invisible dark text on the dark background because the old
hand-rolled QSS had no base QWidget/QLabel color rule, and (2) QDialog and
QMenu content stayed light-on-light because QSS color rules have to be
declared per widget class and these were missed. ThemeManager now drives
theming through a QPalette + the Fusion style instead of per-widget QSS, so
these are asserted broadly (label, dialog, menu) rather than per bug.
"""

import pytest
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QMainWindow, QVBoxLayout

from app.ui.models.ui_enums import UITheme
from app.ui.themes.theme_manager import ThemeManager


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _has_visible_text(image, background_lightness_ceiling: float | None = None) -> bool:
    has_light_pixel = any(
        image.pixelColor(x, y).lightness() > 150
        for x in range(0, image.width(), 2)
        for y in range(0, image.height(), 2)
    )
    if background_lightness_ceiling is None:
        return has_light_pixel
    background_ok = image.pixelColor(3, 3).lightness() < background_lightness_ceiling
    return has_light_pixel and background_ok


@pytest.fixture
def theme_manager(qapp: QApplication) -> ThemeManager:
    manager = ThemeManager()
    yield manager
    manager.apply(UITheme.LIGHT)


class TestUnstyledLabelIsVisible:
    @pytest.mark.parametrize("theme", [UITheme.DARK, UITheme.HIGH_CONTRAST])
    def test_label_in_a_window_is_visible(self, qapp: QApplication, theme_manager: ThemeManager, theme: UITheme) -> None:
        theme_manager.apply(theme)
        window = QMainWindow()
        central = QLabel("Hello World")
        window.setCentralWidget(central)
        window.resize(200, 80)
        window.show()
        qapp.processEvents()

        image = window.grab().toImage()

        assert _has_visible_text(image, background_lightness_ceiling=60)
        window.close()


class TestDialogLabelIsVisible:
    @pytest.mark.parametrize("theme", [UITheme.DARK, UITheme.HIGH_CONTRAST])
    def test_dialog_label_is_visible(self, qapp: QApplication, theme_manager: ThemeManager, theme: UITheme) -> None:
        theme_manager.apply(theme)
        dialog = QDialog()
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Underlying"))
        dialog.resize(200, 80)
        dialog.show()
        qapp.processEvents()

        image = dialog.grab().toImage()

        assert _has_visible_text(image, background_lightness_ceiling=60)
        dialog.close()


class TestMenuIsVisible:
    @pytest.mark.parametrize("theme", [UITheme.DARK, UITheme.HIGH_CONTRAST])
    def test_menu_popup_is_visible(self, qapp: QApplication, theme_manager: ThemeManager, theme: UITheme) -> None:
        theme_manager.apply(theme)
        window = QMainWindow()
        file_menu = window.menuBar().addMenu("File")
        file_menu.addAction("Open")
        file_menu.addAction("Save")
        window.resize(300, 200)
        window.show()
        file_menu.setGeometry(50, 50, 150, 80)
        qapp.processEvents()

        image = file_menu.grab().toImage()

        assert _has_visible_text(image, background_lightness_ceiling=60)
        window.close()


class TestLightThemeRestoresNativeLook:
    def test_dark_then_light_round_trips_to_the_pre_theme_style_and_palette(
        self, qapp: QApplication, theme_manager: ThemeManager,
    ) -> None:
        """Whatever style/palette was active immediately before the first
        apply() call must come back after DARK -> LIGHT -- captured fresh
        here rather than compared against a hardcoded style name, since a
        prior test in the same session may have already left Fusion active
        (QApplication's style is a process-wide singleton across tests)."""
        style_before = qapp.style().objectName()
        palette_before = QPalette(qapp.palette())

        theme_manager.apply(UITheme.DARK)
        theme_manager.apply(UITheme.LIGHT)

        assert qapp.style().objectName() == style_before
        assert qapp.palette() == palette_before
