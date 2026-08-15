"""Tests for Breeze option chain CALL/PUT request behavior."""

from decimal import Decimal

import pytest

from app.brokers.breeze.option_chain import BreezeOptionChain
from app.brokers.shared.enums import OptionRight
from app.brokers.shared.models import OptionChainRequest
from app.exceptions.broker_exception import BrokerException


class _RecordingClient:
    """Records get_option_chain_quotes calls and returns canned rows by side."""

    def __init__(self, rows_by_right: dict[str, list[dict]]) -> None:
        self._rows_by_right = rows_by_right
        self.calls: list[dict] = []

    def get_option_chain_quotes(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        return {"Success": self._rows_by_right.get(kwargs["right"], [])}


class _ErrorOnCallClient:
    """Returns a Breeze-style {"Error": ...} response for the CALL request only."""

    def __init__(self, error_message: str) -> None:
        self._error_message = error_message
        self.calls: list[dict] = []

    def get_option_chain_quotes(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        if kwargs["right"] == "call":
            return {"Success": "", "Status": 500, "Error": self._error_message}
        return {"Success": [], "Status": 200, "Error": None}


def _row(strike: str, right: str, **extra) -> dict:
    row = {
        "strike_price": strike,
        "right": right,
        "stock_code": f"NIFTY{strike}{right.upper()}",
        "ltp": "100",
        "best_bid_price": "99",
        "best_offer_price": "101",
        "open_interest": "5000",
        "total_quantity_traded": "12000",
    }
    row.update(extra)
    return row


def test_full_chain_request_performs_call_and_put_requests() -> None:
    client = _RecordingClient(
        {"call": [_row("24500", "call")], "put": [_row("24500", "put")]}
    )
    service = BreezeOptionChain(client)
    request = OptionChainRequest(underlying="NIFTY", exchange="NFO", expiry_date="13-Feb-2026")

    chain = service.get_option_chain(request)

    assert [call["right"] for call in client.calls] == ["call", "put"]
    for call in client.calls:
        assert call["stock_code"] == "NIFTY"
        # Breeze's get_option_chain_quotes() (unlike get_quotes()) requires
        # uppercase exchange_code and an ISO-8601 expiry_date — see the
        # bundled SDK's own documented CALL/PUT examples.
        assert call["exchange_code"] == "NFO"
        assert call["expiry_date"] == "2026-02-13T06:00:00.000Z"
        assert call["product_type"] == "options"
        assert call["strike_price"] == ""
    assert len(chain.rows) == 1


def test_explicit_call_request_performs_only_call_request() -> None:
    client = _RecordingClient({"call": [_row("24500", "call")]})
    service = BreezeOptionChain(client)
    request = OptionChainRequest(
        underlying="NIFTY", exchange="NFO", expiry_date="13-Feb-2026", right=OptionRight.CALL
    )

    service.get_option_chain(request)

    assert len(client.calls) == 1
    assert client.calls[0]["right"] == "call"


def test_explicit_put_request_performs_only_put_request() -> None:
    client = _RecordingClient({"put": [_row("24500", "put")]})
    service = BreezeOptionChain(client)
    request = OptionChainRequest(
        underlying="NIFTY", exchange="NFO", expiry_date="13-Feb-2026", right=OptionRight.PUT
    )

    service.get_option_chain(request)

    assert len(client.calls) == 1
    assert client.calls[0]["right"] == "put"


def test_full_chain_with_multiple_strikes_does_not_request_per_strike() -> None:
    """Only two requests total (CALL, PUT) regardless of strike count."""
    client = _RecordingClient(
        {
            "call": [_row("24500", "call"), _row("24600", "call"), _row("24700", "call")],
            "put": [_row("24500", "put"), _row("24600", "put"), _row("24700", "put")],
        }
    )
    service = BreezeOptionChain(client)
    request = OptionChainRequest(underlying="NIFTY", exchange="NFO", expiry_date="13-Feb-2026")

    chain = service.get_option_chain(request)

    assert len(client.calls) == 2
    assert len(chain.rows) == 3


class TestExpiryDateConvertedToIso8601:
    """get_option_chain_quotes() requires ISO-8601 expiry_date, unlike get_quotes()."""

    def test_dd_mon_yyyy_expiry_is_converted_to_iso8601(self) -> None:
        client = _RecordingClient({"call": [], "put": []})
        service = BreezeOptionChain(client)
        request = OptionChainRequest(underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026")

        service.get_option_chain(request)

        assert all(call["expiry_date"] == "2026-08-18T06:00:00.000Z" for call in client.calls)

    def test_exchange_code_is_sent_uppercase(self) -> None:
        client = _RecordingClient({"call": [], "put": []})
        service = BreezeOptionChain(client)
        request = OptionChainRequest(underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026")

        service.get_option_chain(request)

        assert all(call["exchange_code"] == "NFO" for call in client.calls)

    def test_normalizer_still_receives_original_dd_mon_yyyy_expiry(self) -> None:
        """The ISO conversion is local to the outgoing SDK request only —
        cache keys/normalizer/UI must keep seeing the original format."""
        client = _RecordingClient(
            {"call": [_row("24500", "call")], "put": [_row("24500", "put")]}
        )
        service = BreezeOptionChain(client)
        request = OptionChainRequest(underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026")

        chain = service.get_option_chain(request)

        assert chain.expiry_date == "18-Aug-2026"


class TestBreezeErrorResponseSurfaces:
    """A Breeze {"Error": ...} response must raise, not be swallowed.

    Direct reproduction of the live failure: the CALL request's SDK call
    returns successfully (no exception, no hang) but with an Error payload
    (e.g. "Error while calling service, Please contact admin (T10:55)").
    unwrap_success() must raise for it, and BreezeOptionChain must not go
    on to request PUT afterwards.
    """

    def test_error_response_on_call_request_raises_broker_exception(self) -> None:
        client = _ErrorOnCallClient("Error while calling service, Please contact admin (T10:55)")
        service = BreezeOptionChain(client)
        request = OptionChainRequest(underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026")

        with pytest.raises(BrokerException, match="Please contact admin"):
            service.get_option_chain(request)

    def test_error_response_on_call_request_stops_before_put(self) -> None:
        client = _ErrorOnCallClient("Error while calling service, Please contact admin (T10:55)")
        service = BreezeOptionChain(client)
        request = OptionChainRequest(underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026")

        with pytest.raises(BrokerException):
            service.get_option_chain(request)

        assert [call["right"] for call in client.calls] == ["call"]


class _NoneErrorKeyClient:
    """Returns Breeze's normal successful envelope, which always includes a
    present-but-None "Error" key (per Breeze's own documented response
    shape: {"Success": [...], "Status": 200, "Error": None})."""

    def __init__(self, rows_by_right: dict[str, list[dict]]) -> None:
        self._rows_by_right = rows_by_right
        self.calls: list[dict] = []

    def get_option_chain_quotes(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        return {
            "Success": self._rows_by_right.get(kwargs["right"], []),
            "Status": 200,
            "Error": None,
        }


class TestSuccessResponseWithNoneErrorIsProcessed:
    """Regression coverage for the unwrap_success() fix.

    Live-confirmed root cause: unwrap_success() checked `"Error" in
    response`, true even when the value is None. Breeze's documented
    successful response envelope always includes an "Error" key set to
    None, so every successful CALL response was misread as an error,
    raising BrokerException("None") before PUT could ever be requested.
    fix: unwrap_success() now checks response.get("Error") truthiness.
    These tests prove a CALL response with Error=None no longer raises,
    proceeds to normalization, and lets the loop continue to PUT.
    """

    def test_call_response_with_none_error_does_not_raise(self) -> None:
        client = _NoneErrorKeyClient({"call": [_row("24500", "call")]})
        service = BreezeOptionChain(client)
        request = OptionChainRequest(
            underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026", right=OptionRight.CALL
        )

        chain = service.get_option_chain(request)

        assert len(chain.rows) == 1

    def test_call_and_put_responses_with_none_error_are_both_requested_and_merged(
        self,
    ) -> None:
        """Integration-level proof: CALL Error=None + PUT Error=None ->
        exactly one CALL request, one PUT request, and both sides' rows
        merged into the returned chain."""
        client = _NoneErrorKeyClient(
            {"call": [_row("24500", "call")], "put": [_row("24500", "put")]}
        )
        service = BreezeOptionChain(client)
        request = OptionChainRequest(underlying="NIFTY", exchange="NFO", expiry_date="18-Aug-2026")

        chain = service.get_option_chain(request)

        assert [call["right"] for call in client.calls] == ["call", "put"]
        assert len(client.calls) == 2
        assert len(chain.rows) == 1
        assert chain.rows[0].strike_price == Decimal("24500")
