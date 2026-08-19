"""Tests for OpenDialog: a picker over real (id, name) pairs, not a
free-text id box -- the caller (Strategy Builder's Load button, ribbon's
Open button) already knows the valid ids from list_strategies()."""

import pytest
from PySide6.QtWidgets import QApplication

from app.ui.dialogs.open_dialog import OpenDialog


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


class TestOpenDialogSelection:
    def test_first_item_is_preselected(self, qapp: QApplication) -> None:
        dialog = OpenDialog([("a", "Iron Condor"), ("b", "Straddle")])

        assert dialog.selected_id() == "a"

    def test_selecting_a_different_row_changes_selected_id(self, qapp: QApplication) -> None:
        dialog = OpenDialog([("a", "Iron Condor"), ("b", "Straddle")])

        dialog._list.setCurrentRow(1)

        assert dialog.selected_id() == "b"

    def test_empty_items_returns_empty_string(self, qapp: QApplication) -> None:
        dialog = OpenDialog([])

        assert dialog.selected_id() == ""

    def test_falls_back_to_id_when_name_is_blank(self, qapp: QApplication) -> None:
        dialog = OpenDialog([("strat-1", "")])

        assert dialog._list.item(0).text() == "strat-1"
        assert dialog.selected_id() == "strat-1"
