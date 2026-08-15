"""Regression tests for unwrap_success() Error-value truthiness fix.

Bug: unwrap_success() checked `"Error" in response` (key presence), but
Breeze's response envelope always includes an "Error" key, set to None on
success (e.g. {"Success": [...], "Status": 200, "Error": None}). Every
successful Breeze response was therefore misread as an error, raising
BrokerException("None") — confirmed live for get_option_chain_quotes(),
where a genuinely successful CALL response with real NIFTY option-chain
rows was discarded before ever reaching the normalizer, and PUT was never
requested.

Fix: check response.get("Error") truthiness instead of key presence.
"""

import pytest

from app.brokers.breeze.utilities import unwrap_success
from app.exceptions.broker_exception import BrokerException


class TestUnwrapSuccessErrorNone:
    """(a) Error=None is success — the exact live-confirmed Breeze envelope."""

    def test_error_none_returns_success_payload(self) -> None:
        response = {
            "Success": [{"strike_price": "24500", "right": "call"}],
            "Status": 200,
            "Error": None,
        }

        payload = unwrap_success(response)

        assert payload == [{"strike_price": "24500", "right": "call"}]


class TestUnwrapSuccessErrorEmptyString:
    """(b) Error="" is success."""

    def test_error_empty_string_returns_success_payload(self) -> None:
        response = {"Success": [{"strike_price": "24500"}], "Status": 200, "Error": ""}

        payload = unwrap_success(response)

        assert payload == [{"strike_price": "24500"}]


class TestUnwrapSuccessErrorFalse:
    """Error=False is success (per the stated intended-behavior contract)."""

    def test_error_false_returns_success_payload(self) -> None:
        response = {"Success": [{"strike_price": "24500"}], "Status": 200, "Error": False}

        payload = unwrap_success(response)

        assert payload == [{"strike_price": "24500"}]


class TestUnwrapSuccessActualError:
    """(c) A truthy Error value must still raise BrokerException with that message."""

    def test_truthy_error_raises_broker_exception_with_message(self) -> None:
        response = {
            "Success": "",
            "Status": 500,
            "Error": "Error while calling service, Please contact admin (T10:55)",
        }

        with pytest.raises(BrokerException) as excinfo:
            unwrap_success(response)

        assert str(excinfo.value) == "Error while calling service, Please contact admin (T10:55)"


class TestUnwrapSuccessMissingErrorKey:
    """(d) Missing Error key preserves existing (pre-fix) behavior."""

    def test_missing_error_key_returns_success_payload(self) -> None:
        response = {"Success": [{"strike_price": "24500"}]}

        payload = unwrap_success(response)

        assert payload == [{"strike_price": "24500"}]


class TestUnwrapSuccessMalformedResponseUnchanged:
    """(e) Existing malformed/invalid response fallback behavior is unchanged."""

    def test_missing_success_key_returns_whole_response(self) -> None:
        """No "Success" key at all: falls back to returning the whole dict,
        exactly as before (response.get("Success", response))."""
        response = {"Status": 200}

        payload = unwrap_success(response)

        assert payload == {"Status": 200}

    def test_error_still_truthy_string_raises(self) -> None:
        """Pre-existing regression coverage (test_broker_extended.py) must
        keep passing: a bare {"Error": "failed"} response still raises."""
        with pytest.raises(BrokerException):
            unwrap_success({"Error": "failed"})
