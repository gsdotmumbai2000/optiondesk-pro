"""Tests for the Settings tab's Save flow: previously save_preferences()
re-fetched and re-saved whatever was already stored, so editing the
Default Exchange field (or the new Show Greeks checkbox) and clicking Save
had no observable effect. The View must now build the UserPreferences from
its own current widget state and hand it to the ViewModel to persist.
"""

import pytest
from PySide6.QtWidgets import QApplication

from app.application.models.session import UserPreferences
from app.ui.settings.settings_view import SettingsView


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


class _FakeCommand:
    def execute(self) -> None:
        pass


class _FakeSettingsViewModel:
    def __init__(self, preferences: UserPreferences) -> None:
        self._preferences = preferences
        self.apply_theme_command = _FakeCommand()
        self.saved: list[UserPreferences] = []
        self.theme_changed = _FakeSignal()

    def get_preferences(self) -> UserPreferences:
        return self._preferences

    def save_preferences(self, preferences: UserPreferences) -> None:
        self.saved.append(preferences)


class _FakeSignal:
    def connect(self, *_args, **_kwargs) -> None:
        pass


class TestSaveBuildsPreferencesFromCurrentFormState:
    def test_editing_the_exchange_field_and_saving_persists_the_new_value(self, qapp: QApplication) -> None:
        vm = _FakeSettingsViewModel(UserPreferences(default_exchange="NSE"))
        view = SettingsView(vm)

        view._exchange.setText("BSE")
        view._on_save_clicked()

        assert vm.saved == [UserPreferences(default_exchange="BSE")]

    def test_checking_show_greeks_and_saving_persists_it(self, qapp: QApplication) -> None:
        vm = _FakeSettingsViewModel(UserPreferences(show_greeks_in_leg_picker=False))
        view = SettingsView(vm)

        view._show_greeks.setChecked(True)
        view._on_save_clicked()

        assert vm.saved[-1].show_greeks_in_leg_picker is True

    def test_form_is_prefilled_from_existing_preferences(self, qapp: QApplication) -> None:
        vm = _FakeSettingsViewModel(UserPreferences(default_exchange="BSE", show_greeks_in_leg_picker=True))

        view = SettingsView(vm)

        assert view._exchange.text() == "BSE"
        assert view._show_greeks.isChecked() is True

    def test_blank_exchange_falls_back_to_nse(self, qapp: QApplication) -> None:
        vm = _FakeSettingsViewModel(UserPreferences(default_exchange="BSE"))
        view = SettingsView(vm)

        view._exchange.setText("   ")
        view._on_save_clicked()

        assert vm.saved[-1].default_exchange == "NSE"
