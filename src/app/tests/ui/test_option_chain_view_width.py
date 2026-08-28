"""Tests for the OptionChainView strike-width combo box."""

import pytest
from PySide6.QtWidgets import QApplication

from app.ui.option_chain.option_chain_view import OptionChainView


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_default_width_selection_is_ten(qapp: QApplication) -> None:
    view = OptionChainView()

    assert view._width.currentData() == 10


def test_changing_width_emits_chain_width_changed(qapp: QApplication) -> None:
    view = OptionChainView()
    emitted: list[int] = []
    view.chain_width_changed.connect(emitted.append)

    view._width.setCurrentIndex(view._width.findData(20))

    assert emitted == [20]


def test_all_offered_widths_are_selectable(qapp: QApplication) -> None:
    view = OptionChainView()

    values = [view._width.itemData(i) for i in range(view._width.count())]

    assert values == [5, 10, 20, 30]
