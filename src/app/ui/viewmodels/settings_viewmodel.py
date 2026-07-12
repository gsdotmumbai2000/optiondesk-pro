"""Settings workspace ViewModel."""

from PySide6.QtCore import Property, Signal

from app.application.models.session import UserPreferences
from app.ui.commands.ui_command import RelayCommand
from app.ui.models.ui_enums import UITheme
from app.ui.themes.theme_manager import ThemeManager
from app.ui.viewmodels.base_viewmodel import BaseViewModel
from app.ui.viewmodels.context import ViewModelContext


class SettingsViewModel(BaseViewModel):
    """ViewModel for settings workspace."""

    theme_changed = Signal(str)

    def __init__(
        self,
        ctx: ViewModelContext,
        theme_manager: ThemeManager,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._ctx = ctx
        self._theme_manager = theme_manager
        self._theme = theme_manager.current_theme.value
        self.apply_theme_command = RelayCommand(self.cycle_theme, parent=self)
        self.save_command = RelayCommand(self.save_preferences, parent=self)

    @Property(str, notify=theme_changed)
    def theme(self) -> str:
        return self._theme

    def cycle_theme(self) -> None:
        nxt = self._theme_manager.cycle()
        self._theme = nxt.value
        self.theme_changed.emit(self._theme)
        self.status_message = f"Theme: {self._theme}"

    def apply_theme(self, theme: UITheme) -> None:
        self._theme_manager.apply(theme)
        self._theme = theme.value
        self.theme_changed.emit(self._theme)

    def save_preferences(self) -> None:
        prefs = self._ctx.provider.settings.get_preferences(self._ctx.session_id)
        self._ctx.provider.settings.update_preferences(self._ctx.session_id, prefs)
        self.status_message = "Preferences saved"

    def get_preferences(self) -> UserPreferences:
        return self._ctx.provider.settings.get_preferences(self._ctx.session_id)
