"""Settings workspace ViewModel."""

from PySide6.QtCore import Property, Signal

from app.application.models.session import UserPreferences
from app.config.models.app_config import MarketMode
from app.ui.commands.ui_command import RelayCommand
from app.ui.models.ui_enums import UITheme
from app.ui.themes.theme_manager import ThemeManager
from app.ui.viewmodels.base_viewmodel import BaseViewModel
from app.ui.viewmodels.context import ViewModelContext


class SettingsViewModel(BaseViewModel):
    """ViewModel for settings workspace."""

    theme_changed = Signal(str)
    market_mode_changed = Signal(dict)

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
        self._market_mode_service = ctx.provider.market_mode_service

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

    @Property(str, notify=market_mode_changed)
    def market_mode(self) -> str:
        """Return the configured mode: auto, live, or simulator."""
        if self._market_mode_service is None:
            return MarketMode.AUTO.value
        return self._market_mode_service.mode.value

    @Property(str, notify=market_mode_changed)
    def active_broker(self) -> str:
        """Return the broker code actually connected right now."""
        if self._market_mode_service is None:
            return ""
        return self._market_mode_service.active_broker_code

    def set_market_mode(self, mode: str) -> None:
        """Switch Live/Simulator/Auto mode, hot-swapping the broker in place."""
        if self._market_mode_service is None:
            self.status_message = "Market mode switching unavailable"
            return
        try:
            effective = self._market_mode_service.apply(MarketMode(mode))
            self.status_message = f"Market mode: {mode} (active broker: {effective})"
        except Exception as error:
            self.set_error(f"Failed to switch market mode: {error}")
            self.status_message = f"Failed to switch market mode: {error}"
        self.market_mode_changed.emit(
            {"mode": self.market_mode, "active_broker": self.active_broker}
        )

    def save_preferences(self, preferences: UserPreferences) -> None:
        """Persist the given preferences (the caller -- SettingsView --
        builds this from the current form state; previously this re-saved
        whatever was already stored, so editing the form and clicking Save
        had no effect)."""
        self._ctx.provider.settings.update_preferences(self._ctx.session_id, preferences)
        self.status_message = "Preferences saved"

    def get_preferences(self) -> UserPreferences:
        return self._ctx.provider.settings.get_preferences(self._ctx.session_id)
