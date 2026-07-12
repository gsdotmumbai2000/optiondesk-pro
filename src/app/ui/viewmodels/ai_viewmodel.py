"""AI workspace ViewModel."""

from PySide6.QtCore import Property, Signal

from app.ui.commands.ui_command import RelayCommand
from app.ui.viewmodels.base_viewmodel import BaseViewModel
from app.ui.viewmodels.context import ViewModelContext


class AIViewModel(BaseViewModel):
    """ViewModel for AI recommendation workspace."""

    recommendations_changed = Signal(list)

    def __init__(self, ctx: ViewModelContext, parent=None) -> None:
        super().__init__(parent)
        self._ctx = ctx
        self._recommendations: list = []
        self.generate_command = RelayCommand(self.generate, parent=self)
        self.history_command = RelayCommand(self.load_history, parent=self)
        self._ctx.events.recommendation_ready.connect(self._on_recommendation_ready)

    @Property(list, notify=recommendations_changed)
    def recommendations(self) -> list:
        return self._recommendations

    def generate(self) -> None:
        self.status_message = "Generate: attach RecommendationAnalysisRequest"

    def load_history(self) -> None:
        result = self._ctx.provider.ai.recommendation_history(self._ctx.session_id)
        self.status_message = result.message

    def explain(self, recommendation) -> str:
        result = self._ctx.provider.ai.explain_recommendation(recommendation)
        return result.message

    def compare(self, recommendations: tuple) -> None:
        result = self._ctx.provider.ai.compare_recommendations(recommendations)
        self._recommendations = list(result.data or [])
        self.recommendations_changed.emit(self._recommendations)

    def _on_recommendation_ready(self, payload: dict) -> None:
        self.status_message = f"Recommendations ready: {payload.get('count', 0)}"
