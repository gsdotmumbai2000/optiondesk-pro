"""Tests for the Breeze stock_code token validation safety check.

Correctness here must not depend on sdk_diagnostics.py: none of these tests
import or call apply_breeze_sdk_diagnostics().
"""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any

import pytest

import app.brokers.breeze.token_validation as token_validation


@pytest.fixture(autouse=True)
def reset_token_validation_patch() -> None:
    """Allow the module patch to run once per test."""
    token_validation._PATCHED = False
    yield
    token_validation._PATCHED = False


def _install_fake_breeze(monkeypatch: pytest.MonkeyPatch, result: Any) -> type:
    class FakeBreezeConnect:
        def get_stock_token_value(self, **kwargs: Any) -> Any:
            return result

    fake_module = ModuleType("breeze_connect.breeze_connect")
    fake_module.BreezeConnect = FakeBreezeConnect
    monkeypatch.setitem(sys.modules, "breeze_connect.breeze_connect", fake_module)
    return FakeBreezeConnect


def test_valid_token_pair_passes_through_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    """A genuinely valid token pair must be returned unchanged."""
    FakeBreezeConnect = _install_fake_breeze(monkeypatch, ("4.1!26000", "4.2!26000"))
    token_validation.apply_breeze_token_validation()

    client = FakeBreezeConnect()
    result = client.get_stock_token_value(exchange_code="NSE", stock_code="NIFTY")

    assert result == ("4.1!26000", "4.2!26000")


def test_exchange_quotes_invalid_token_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """"4.1!False" (get_exchange_quotes token) must be rejected."""
    FakeBreezeConnect = _install_fake_breeze(monkeypatch, ("4.1!False", "4.2!26000"))
    token_validation.apply_breeze_token_validation()

    client = FakeBreezeConnect()
    with pytest.raises(token_validation.BreezeInvalidStockCodeError, match="BANKNIFTY"):
        client.get_stock_token_value(exchange_code="NSE", stock_code="BANKNIFTY")


def test_market_depth_invalid_token_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """"4.2!False" (get_market_depth token) must be rejected."""
    FakeBreezeConnect = _install_fake_breeze(monkeypatch, ("4.1!26000", "4.2!False"))
    token_validation.apply_breeze_token_validation()

    client = FakeBreezeConnect()
    with pytest.raises(token_validation.BreezeInvalidStockCodeError, match="FINNIFTY"):
        client.get_stock_token_value(exchange_code="NSE", stock_code="FINNIFTY")


def test_market_depth_not_requested_is_not_flagged(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_market_depth=False legitimately yields Python False, not a string;
    that must not be mistaken for an invalid token."""
    FakeBreezeConnect = _install_fake_breeze(monkeypatch, ("4.1!26000", False))
    token_validation.apply_breeze_token_validation()

    client = FakeBreezeConnect()
    result = client.get_stock_token_value(
        exchange_code="NSE", stock_code="NIFTY", get_market_depth=False
    )

    assert result == ("4.1!26000", False)


def test_validation_does_not_require_sdk_diagnostics(monkeypatch: pytest.MonkeyPatch) -> None:
    """Protection must hold even when sdk_diagnostics is never applied.

    This test deliberately never imports app.brokers.breeze.sdk_diagnostics
    or calls apply_breeze_sdk_diagnostics(), proving the check is
    self-contained.
    """
    FakeBreezeConnect = _install_fake_breeze(monkeypatch, ("4.1!False", "4.2!False"))

    token_validation.apply_breeze_token_validation()

    client = FakeBreezeConnect()
    with pytest.raises(token_validation.BreezeInvalidStockCodeError, match="MIDCPNIFTY"):
        client.get_stock_token_value(exchange_code="NSE", stock_code="MIDCPNIFTY")


def test_apply_breeze_token_validation_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patching should run once even if called multiple times."""
    FakeBreezeConnect = _install_fake_breeze(monkeypatch, ("4.1!26000", "4.2!26000"))

    token_validation.apply_breeze_token_validation()
    patched_once = FakeBreezeConnect.get_stock_token_value
    token_validation.apply_breeze_token_validation()

    assert FakeBreezeConnect.get_stock_token_value is patched_once
