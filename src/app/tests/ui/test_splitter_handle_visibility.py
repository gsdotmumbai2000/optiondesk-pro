"""Regression test: a QSplitter's drag handle must be visibly distinct from
the surrounding background at rest, not just findable by hunting with the
mouse -- Qt's default Fusion handle has no idle-state color of its own.
"""

import pytest
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter, QWidget

from app.ui.widgets.common import style_splitter_handle


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


class TestStyleSplitterHandle:
    def test_widens_the_handle_for_easier_grabbing(self, qapp: QApplication) -> None:
        splitter = QSplitter()

        style_splitter_handle(splitter)

        assert splitter.handleWidth() >= 6

    def test_applies_an_idle_and_hover_color_rule(self, qapp: QApplication) -> None:
        splitter = QSplitter()

        style_splitter_handle(splitter)

        stylesheet = splitter.styleSheet()
        assert "QSplitter::handle {" in stylesheet
        assert "QSplitter::handle:hover {" in stylesheet

    def test_handle_pixels_differ_from_the_surrounding_background(self, qapp: QApplication) -> None:
        splitter = QSplitter()
        splitter.addWidget(QWidget())
        splitter.addWidget(QWidget())
        style_splitter_handle(splitter)
        window = QMainWindow()
        window.setCentralWidget(splitter)
        window.resize(300, 300)
        window.show()
        qapp.processEvents()

        handle_image = splitter.handle(1).grab().toImage()
        background_image = window.grab().toImage()

        window.close()
        handle_color = handle_image.pixelColor(handle_image.width() // 2, handle_image.height() // 2)
        background_color = background_image.pixelColor(2, 2)
        assert handle_color != background_color
