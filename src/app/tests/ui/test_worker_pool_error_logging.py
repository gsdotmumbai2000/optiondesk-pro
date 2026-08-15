"""Diagnostic tests for WorkerRunnable's enhanced exception logging.

This round only added logging (exception class, repr, args, full traceback
via logger.exception()) around the existing except block in
WorkerRunnable.run(). These tests prove that addition is behavior-neutral:
on_finished/on_error still receive exactly what they did before.
"""

import pytest
from PySide6.QtWidgets import QApplication

from app.exceptions.broker_exception import BrokerException
from app.ui.application.worker_pool import WorkerRunnable, WorkerSignals


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Provide a Qt application instance for signal tests."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


class TestWorkerRunnableSignalsUnchangedByDiagnosticLogging:
    def test_finished_signal_receives_result_on_success(self, qapp: QApplication) -> None:
        signals = WorkerSignals()
        results: list = []
        signals.finished.connect(results.append)

        WorkerRunnable(lambda: "ok", signals).run()

        assert results == ["ok"]

    def test_error_signal_receives_str_of_exception_message(self, qapp: QApplication) -> None:
        signals = WorkerSignals()
        errors: list[str] = []
        signals.error.connect(errors.append)

        def raise_value_error():
            raise ValueError("boom")

        WorkerRunnable(raise_value_error, signals).run()

        assert errors == ["boom"]

    def test_error_signal_receives_literal_none_string_for_none_message(
        self, qapp: QApplication
    ) -> None:
        """Reproduces the exact live symptom: an exception constructed with
        str(None) as its message stringifies to the literal text "None" on
        the error signal — this is unchanged by the new diagnostic logging,
        and matches the live log line
        'WorkerRunnable.run: fn() raised, emitting error: None'."""
        signals = WorkerSignals()
        errors: list[str] = []
        signals.error.connect(errors.append)

        def raise_broker_exception_with_none_message():
            raise BrokerException(str(None))

        WorkerRunnable(raise_broker_exception_with_none_message, signals).run()

        assert errors == ["None"]
