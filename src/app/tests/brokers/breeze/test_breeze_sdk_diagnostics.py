"""Tests for Breeze SDK diagnostic instrumentation."""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any

import pytest

import app.brokers.breeze.sdk_diagnostics as sdk_diagnostics


@pytest.fixture(autouse=True)
def reset_sdk_diagnostics_patch() -> None:
    """Allow diagnostics patching to run once per test."""
    sdk_diagnostics._PATCHED = False
    yield
    sdk_diagnostics._PATCHED = False


def test_apply_breeze_sdk_diagnostics_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Patching should run once and wrap get_stock_token_value."""
    calls: list[str] = []

    class FakeBreezeConnect:
        def get_stock_token_value(self, **kwargs: Any) -> tuple[str, str]:
            calls.append("original")
            return "4.1!123", "4.2!123"

    fake_module = ModuleType("breeze_connect.breeze_connect")
    fake_module.BreezeConnect = FakeBreezeConnect
    monkeypatch.setitem(sys.modules, "breeze_connect.breeze_connect", fake_module)

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
    assert result == ("4.1!123", "4.2!123")
    assert calls == ["original"]
    assert "exchange_code" in captured.out
    assert "stock_code" in captured.out
    assert "NIFTY" in captured.out
    assert "stock_script_dict_list exists: True" in captured.out
    assert "NSE dictionary entries: 1" in captured.out
    assert "requested stock_code exists in NSE dictionary: True" in captured.out


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
