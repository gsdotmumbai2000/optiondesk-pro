"""Tests for AIViewModel.generate(): the "Generate Recommendation" action
wired to AIWorkspaceService.generate_recommendation_for_active_strategy(),
run off the Qt UI thread via BackgroundWorker.
"""

from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from app.application.models.enums import WorkspaceType
from app.application.models.workspace import WorkspaceOperationResult
from app.ui.viewmodels.ai_viewmodel import AIViewModel
from app.ui.viewmodels.context import ViewModelContext


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


class _FakeWorker:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def run(self, fn, on_finished, on_error) -> None:
        self.calls.append((fn, on_finished, on_error))

    def execute(self, index: int = -1) -> None:
        fn, done, err = self.calls[index]
        try:
            result = fn()
        except Exception as exc:  # noqa: BLE001
            err(str(exc))
            return
        done(result)


class _FakeAIService:
    def __init__(self, result: WorkspaceOperationResult) -> None:
        self.result = result
        self.calls: list[str] = []

    def generate_recommendation_for_active_strategy(self, session_id: str, exchange: str = "NFO") -> WorkspaceOperationResult:
        self.calls.append(session_id)
        return self.result


def _fake_events() -> SimpleNamespace:
    """AIViewModel.__init__ connects to events.recommendation_ready."""
    return SimpleNamespace(recommendation_ready=SimpleNamespace(connect=lambda *a, **k: None))


def _batch(recommendations=()):
    return SimpleNamespace(recommendations=recommendations, primary=None)


def _make_viewmodel(ai: _FakeAIService) -> tuple[AIViewModel, _FakeWorker]:
    provider = SimpleNamespace(ai=ai)
    worker = _FakeWorker()
    ctx = ViewModelContext(provider=provider, worker=worker, events=_fake_events(), session_id="s1")
    vm = AIViewModel(ctx)
    return vm, worker


class TestGenerateSuccess:
    def test_dispatches_to_background_worker_not_ui_thread(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.AI, "1 recommendation(s) generated", _batch())
        ai = _FakeAIService(result)
        vm, worker = _make_viewmodel(ai)

        vm.generate()

        assert len(worker.calls) == 1
        assert ai.calls == []  # not called yet -- only queued

    def test_busy_true_while_pending_false_after_completion(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.AI, "generated", _batch())
        vm, worker = _make_viewmodel(_FakeAIService(result))

        vm.generate()
        assert vm.busy is True
        worker.execute()
        assert vm.busy is False

    def test_emits_recommendations_changed_with_recommendations(self, qapp: QApplication) -> None:
        recs = [SimpleNamespace(name="r1"), SimpleNamespace(name="r2")]
        result = WorkspaceOperationResult(True, WorkspaceType.AI, "generated", _batch(recommendations=tuple(recs)))
        vm, worker = _make_viewmodel(_FakeAIService(result))
        received: list = []
        vm.recommendations_changed.connect(received.append)

        vm.generate()
        worker.execute()

        assert received == [recs]
        assert vm.recommendations == recs

    def test_status_message_reflects_success(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.AI, "1 recommendation(s) generated", _batch())
        vm, worker = _make_viewmodel(_FakeAIService(result))

        vm.generate()
        worker.execute()

        assert vm.status_message == "1 recommendation(s) generated"

    def test_passes_configured_session_id_to_service(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(True, WorkspaceType.AI, "generated", _batch())
        ai = _FakeAIService(result)
        vm, worker = _make_viewmodel(ai)

        vm.generate()
        worker.execute()

        assert ai.calls == ["s1"]


class TestGenerateUnavailableFallsBackGracefully:
    def test_no_active_strategy_sets_status_message_without_crashing(self, qapp: QApplication) -> None:
        result = WorkspaceOperationResult(False, WorkspaceType.AI, "No active strategy to generate recommendations for")
        vm, worker = _make_viewmodel(_FakeAIService(result))
        received: list = []
        vm.recommendations_changed.connect(received.append)

        vm.generate()
        worker.execute()

        assert vm.status_message == "No active strategy to generate recommendations for"
        assert received == []


class TestGenerateErrorPath:
    def test_service_exception_sets_error_not_crash(self, qapp: QApplication) -> None:
        class _RaisingAIService:
            def generate_recommendation_for_active_strategy(self, session_id: str, exchange: str = "NFO"):
                raise RuntimeError("ai engine unavailable")

        provider = SimpleNamespace(ai=_RaisingAIService())
        worker = _FakeWorker()
        ctx = ViewModelContext(provider=provider, worker=worker, events=_fake_events(), session_id="s1")
        vm = AIViewModel(ctx)
        errors: list[str] = []
        vm.error_occurred.connect(errors.append)

        vm.generate()
        worker.execute()

        assert vm.busy is False
        assert errors == ["ai engine unavailable"]
