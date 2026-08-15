"""Regression tests for BackgroundWorker's GUI-thread result delivery.

Task 13 root cause: BackgroundWorker.run() connected WorkerSignals.finished/
error directly to plain Python closures. Qt can only auto-marshal a signal
emitted from a QThreadPool worker thread onto the GUI thread when it knows
the receiver's thread affinity via a real QObject; a bare closure has none,
so the connection collapsed to a same-thread DirectConnection and callbacks
ran on the emitting worker thread instead of the GUI thread -- which is why
MarketViewModel.done() never visibly completed and the option chain table
stayed empty.

These tests exercise the REAL QThreadPool (never calling WorkerRunnable.run()
directly on the test thread), so they only pass if delivery is genuinely
marshaled across threads by Qt itself.
"""

import threading
import time

import pytest
from PySide6.QtCore import QCoreApplication, QThread
from PySide6.QtWidgets import QApplication

from app.ui.application.worker_pool import BackgroundWorker


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Provide a Qt application instance for cross-thread signal tests."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _pump_until(predicate, timeout: float = 5.0) -> bool:
    """Drain the Qt event loop until predicate() is true or timeout elapses.

    Test-only helper: a queued cross-thread signal is only delivered while
    the receiving thread's event loop runs, so the test must pump it. This
    is not a stand-in for anything in production -- BackgroundWorker itself
    contains no polling or sleeps.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QCoreApplication.processEvents()
        if predicate():
            return True
        time.sleep(0.01)
    return False


class TestSuccessCallbackRunsOnGuiThread:
    """Test 1: work runs on a worker thread, on_finished runs on the GUI thread."""

    def test_work_and_callback_execute_on_different_threads(
        self, qapp: QApplication
    ) -> None:
        gui_qthread = QCoreApplication.instance().thread()
        work_seen: dict = {}
        callback_seen: dict = {}
        done = threading.Event()

        def work():
            work_seen["python_thread"] = threading.current_thread()
            work_seen["qthread"] = QThread.currentThread()
            return {"strikes": 21}

        def on_finished(result):
            callback_seen["python_thread"] = threading.current_thread()
            callback_seen["qthread"] = QThread.currentThread()
            callback_seen["result"] = result
            done.set()

        def on_error(message):
            pytest.fail(f"unexpected error callback: {message}")

        BackgroundWorker().run(work, on_finished, on_error)

        assert _pump_until(done.is_set), "on_finished was never delivered"

        # The work function must NOT run on the GUI/main thread (it must
        # not block the UI) ...
        assert work_seen["python_thread"] is not threading.main_thread()
        assert work_seen["qthread"] is not gui_qthread

        # ... but the completion callback MUST run on the GUI/main thread,
        # provably via Qt's own thread-affinity API, not just Python's.
        assert callback_seen["python_thread"] is threading.main_thread()
        assert callback_seen["qthread"] is gui_qthread
        assert callback_seen["result"] == {"strikes": 21}


class TestErrorCallbackRunsOnGuiThread:
    """Test 2: a raising work function still delivers on_error on the GUI thread."""

    def test_worker_exception_delivers_error_on_gui_thread_without_crash(
        self, qapp: QApplication
    ) -> None:
        gui_qthread = QCoreApplication.instance().thread()
        callback_seen: dict = {}
        done = threading.Event()

        def work():
            raise ValueError("simulated Breeze failure")

        def on_finished(result):
            pytest.fail(f"unexpected success callback: {result}")

        def on_error(message):
            callback_seen["python_thread"] = threading.current_thread()
            callback_seen["qthread"] = QThread.currentThread()
            callback_seen["message"] = message
            done.set()

        BackgroundWorker().run(work, on_finished, on_error)

        assert _pump_until(done.is_set), "on_error was never delivered"

        assert callback_seen["python_thread"] is threading.main_thread()
        assert callback_seen["qthread"] is gui_qthread
        assert callback_seen["message"] == "simulated Breeze failure"

        # Reaching this line at all proves the app did not crash/abort:
        # a raw cross-thread widget/property mutation inside a slot that
        # Qt/PySide's C++ layer rejects can otherwise terminate the process
        # or corrupt state silently.
        QCoreApplication.processEvents()


class TestCallbackExceptionIsLoggedNotSwallowed:
    """Test 5: an exception raised *inside* a completion callback must be
    visible through the app's own logger, never disappear silently."""

    def test_on_finished_exception_is_logged(
        self, qapp: QApplication, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.ui.application import worker_pool

        logged: list[tuple] = []
        monkeypatch.setattr(
            worker_pool.logger,
            "exception",
            lambda *args, **kwargs: logged.append((args, kwargs)),
        )

        done = threading.Event()

        def work():
            return "ok"

        def on_finished(result):
            done.set()
            raise RuntimeError("boom inside callback")

        def on_error(message):
            pytest.fail(f"unexpected error callback: {message}")

        BackgroundWorker().run(work, on_finished, on_error)

        assert _pump_until(done.is_set), "on_finished was never delivered"
        # give the exception path inside _deliver_finished a chance to log
        assert _pump_until(
            lambda: any("on_finished callback raised" in call[0][0] for call in logged)
        )

        assert any("on_finished callback raised" in call[0][0] for call in logged)

    def test_on_error_exception_is_logged(
        self, qapp: QApplication, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.ui.application import worker_pool

        logged: list[tuple] = []
        monkeypatch.setattr(
            worker_pool.logger,
            "exception",
            lambda *args, **kwargs: logged.append((args, kwargs)),
        )

        done = threading.Event()

        def work():
            raise ValueError("original failure")

        def on_finished(result):
            pytest.fail(f"unexpected success callback: {result}")

        def on_error(message):
            done.set()
            raise RuntimeError("boom inside error callback")

        BackgroundWorker().run(work, on_finished, on_error)

        assert _pump_until(done.is_set), "on_error was never delivered"
        # Two exceptions are expected to be logged here: WorkerRunnable's own
        # pre-existing log of the *original* work() failure, and this test's
        # target -- the callback-raised exception from _deliver_error.
        assert _pump_until(
            lambda: any("on_error callback raised" in call[0][0] for call in logged)
        )

        assert any("on_error callback raised" in call[0][0] for call in logged)


class TestWorkerSignalsBackwardCompatibility:
    """WorkerSignals() with no callbacks must behave exactly as before:
    a plain QObject exposing bare finished/error signals for direct
    same-thread .connect() use (existing WorkerRunnable tests rely on this)."""

    def test_no_arg_construction_still_exposes_plain_signals(
        self, qapp: QApplication
    ) -> None:
        from app.ui.application.worker_pool import WorkerRunnable, WorkerSignals

        signals = WorkerSignals()
        results: list = []
        signals.finished.connect(results.append)

        WorkerRunnable(lambda: "ok", signals).run()

        assert results == ["ok"]
