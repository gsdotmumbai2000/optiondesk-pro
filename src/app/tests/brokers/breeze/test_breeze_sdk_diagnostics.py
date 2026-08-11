"""Tests for Breeze SDK diagnostic instrumentation."""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any

import pytest
from loguru import logger as loguru_logger

import app.brokers.breeze.sdk_diagnostics as sdk_diagnostics


@pytest.fixture(autouse=True)
def reset_sdk_diagnostics_patch() -> None:
    """Allow diagnostics patching to run once per test."""
    sdk_diagnostics._PATCHED = False
    yield
    sdk_diagnostics._PATCHED = False


@pytest.fixture
def captured_logs():
    """Capture Loguru output emitted during the test, independent of stdout."""
    messages: list[str] = []
    sink_id = loguru_logger.add(lambda message: messages.append(str(message)), level="DEBUG")
    yield messages
    loguru_logger.remove(sink_id)


def _install_fake_breeze(monkeypatch: pytest.MonkeyPatch, calls: list[str]) -> type:
    class FakeBreezeConnect:
        def get_stock_token_value(self, **kwargs: Any) -> tuple[str, str]:
            calls.append("original")
            return "4.1!123", "4.2!123"

    fake_module = ModuleType("breeze_connect.breeze_connect")
    fake_module.BreezeConnect = FakeBreezeConnect
    monkeypatch.setitem(sys.modules, "breeze_connect.breeze_connect", fake_module)
    return FakeBreezeConnect


def test_apply_breeze_sdk_diagnostics_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    captured_logs: list[str],
) -> None:
    """Patching should run once and wrap get_stock_token_value."""
    calls: list[str] = []
    FakeBreezeConnect = _install_fake_breeze(monkeypatch, calls)

    sdk_diagnostics.apply_breeze_sdk_diagnostics()
    sdk_diagnostics.apply_breeze_sdk_diagnostics()

    client = FakeBreezeConnect()
    client.stock_script_dict_list = [{"BSE1": "1"}, {"NIFTY": "26000"}]
    result = client.get_stock_token_value(
        exchange_code="nse",
        stock_code="NIFTY",
        product_type="cash",
        get_exchange_quotes=True,
        get_market_depth=False,
    )

    captured = capsys.readouterr()
    log_text = "".join(captured_logs)
    assert result == ("4.1!123", "4.2!123")
    assert calls == ["original"]
    assert "exchange_code" in captured.out
    assert "stock_code" in captured.out
    assert "NIFTY" in captured.out
    assert "stock_script_dict_list exists: True" in log_text
    assert "NSE dictionary entries: 1" in log_text
    assert (
        "requested stock_code exists in NSE dictionary: stock_code=NIFTY exists=True"
        in log_text
    )


@pytest.mark.parametrize(
    ("stock_code", "expected_exists"),
    [
        ("NIFTY", True),
        ("BANKNIFTY", False),
        ("FINNIFTY", False),
        ("MIDCPNIFTY", False),
    ],
)
def test_lookup_state_reports_nse_dictionary_membership_per_index(
    monkeypatch: pytest.MonkeyPatch,
    captured_logs: list[str],
    stock_code: str,
    expected_exists: bool,
) -> None:
    """Diagnostic should report, per index symbol, whether Breeze's own NSE
    cash scrip dictionary actually contains that stock_code."""
    calls: list[str] = []
    FakeBreezeConnect = _install_fake_breeze(monkeypatch, calls)

    sdk_diagnostics.apply_breeze_sdk_diagnostics()

    client = FakeBreezeConnect()
    # Reproduces the suspected production scenario: Breeze's own scrip
    # dictionary only carries a "NIFTY" entry under the NSE cash segment.
    client.stock_script_dict_list = [{}, {"NIFTY": "26000"}]
    client.get_stock_token_value(
        exchange_code="nse",
        stock_code=stock_code,
        product_type="cash",
        get_exchange_quotes=True,
        get_market_depth=False,
    )

    log_text = "".join(captured_logs)
    assert (
        f"requested stock_code exists in NSE dictionary: "
        f"stock_code={stock_code} exists={expected_exists}"
    ) in log_text
    if not expected_exists:
        assert "first 50 available NSE keys" in log_text
        assert "NIFTY" in log_text


def test_apply_breeze_sdk_diagnostics_reraises_returned_exception(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """SDK exception objects returned instead of raised should be re-raised."""
    class FakeBreezeConnect:
        def get_stock_token_value(self, **kwargs: Any) -> RuntimeError:
            return RuntimeError("hidden sdk failure")

    fake_module = ModuleType("breeze_connect.breeze_connect")
    fake_module.BreezeConnect = FakeBreezeConnect
    monkeypatch.setitem(sys.modules, "breeze_connect.breeze_connect", fake_module)

    sdk_diagnostics.apply_breeze_sdk_diagnostics()

    client = FakeBreezeConnect()
    client.stock_script_dict_list = [{}, {}]

    with pytest.raises(RuntimeError, match="hidden sdk failure"):
        client.get_stock_token_value(stock_code="NIFTY", exchange_code="nse")

    captured = capsys.readouterr()
    assert "BREEZE SDK INTERNAL EXCEPTION" in captured.out
    assert "hidden sdk failure" in captured.out
