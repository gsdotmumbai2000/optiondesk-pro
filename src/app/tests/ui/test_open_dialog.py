"""Tests for OpenDialog: a picker over real (id, name) pairs, not a
free-text id box -- the caller (Strategy Builder's Load button, ribbon's
Open button) already knows the valid ids from list_strategies()."""

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

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


class TestOpenDialogDelete:
    def test_no_delete_button_wired_without_callback(self, qapp: QApplication) -> None:
        dialog = OpenDialog([("a", "Iron Condor")])

        assert dialog._on_delete is None

    def test_confirmed_delete_calls_callback_and_removes_row(
        self, qapp: QApplication, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        deleted: list[str] = []
        dialog = OpenDialog(
            [("a", "Iron Condor"), ("b", "Straddle")],
            on_delete=lambda item_id: deleted.append(item_id) or True,
        )
        monkeypatch.setattr(
            QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes,
        )

        dialog._delete_selected()

        assert deleted == ["a"]
        assert dialog._list.count() == 1
        assert dialog.selected_id() == "b"

    def test_declined_confirmation_does_not_delete(
        self, qapp: QApplication, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        deleted: list[str] = []
        dialog = OpenDialog(
            [("a", "Iron Condor")],
            on_delete=lambda item_id: deleted.append(item_id) or True,
        )
        monkeypatch.setattr(
            QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.No,
        )

        dialog._delete_selected()

        assert deleted == []
        assert dialog._list.count() == 1

    def test_failed_delete_keeps_row(self, qapp: QApplication, monkeypatch: pytest.MonkeyPatch) -> None:
        dialog = OpenDialog([("a", "Iron Condor")], on_delete=lambda item_id: False)
        monkeypatch.setattr(
            QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes,
        )
        monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: None)

        dialog._delete_selected()

        assert dialog._list.count() == 1
