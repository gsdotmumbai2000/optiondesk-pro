"""Tests for the Breeze margin_calculator adapter (normalization + payload
mapping). Field names in fixtures match the documented Breeze Margin
Calculator API response: span_margin_required, non_span_margin_required,
order_margin.
"""

from decimal import Decimal
from typing import Any

from app.brokers.breeze.margin import BreezeMargin
from app.brokers.breeze.normalizers.margin_normalizer import normalize_margin
from app.brokers.shared.enums import OptionRight, OrderSide, OrderType, ProductType
from app.brokers.shared.models import OrderRequest


class TestNormalizeMargin:
    def test_maps_documented_response_fields(self) -> None:
        payload = {
            "margin_calulation": [{"stock_code": "NIFTY"}],
            "non_span_margin_required": "5000",
            "order_value": "0",
            "order_margin": "15000",
            "trade_margin": None,
            "block_trade_margin": "0",
            "span_margin_required": "10000",
        }

        margins = normalize_margin(payload, "NFO")

        assert margins.exchange == "NFO"
        assert margins.span_margin == Decimal("10000")
        assert margins.exposure_margin == Decimal("5000")
        assert margins.total_margin == Decimal("15000")
        assert margins.additional_margin == Decimal("0")

    def test_falls_back_to_span_plus_exposure_when_order_margin_missing(self) -> None:
        payload = {
            "non_span_margin_required": "5000",
            "span_margin_required": "10000",
        }

        margins = normalize_margin(payload, "NFO")

        assert margins.total_margin == Decimal("15000")

    def test_present_but_zero_span_is_a_real_zero_not_unavailable(self) -> None:
        """A genuinely present "0" (not null) is a real computed answer,
        distinct from the null case below."""
        payload = {"span_margin_required": "0", "non_span_margin_required": "0", "order_margin": "0"}

        margins = normalize_margin(payload, "NFO")

        assert margins is not None
        assert margins.span_margin == Decimal("0")
        assert margins.total_margin == Decimal("0")


class TestNormalizeMarginUnavailable:
    """Confirmed live against a real account on a non-trading day: Breeze
    returned span_margin_required=null (order_margin="0", not null) for a
    real, correctly-formed position -- the request was understood (a real
    order_value came back) but no margin was actually computed. Treating
    that as a confident "0 margin required" would be actively misleading,
    not just incomplete.
    """

    def test_null_span_margin_required_returns_none(self) -> None:
        payload = {
            "non_span_margin_required": "0",
            "order_value": "477816.11",
            "order_margin": "0",
            "trade_margin": "0",
            "block_trade_margin": "0",
            "span_margin_required": None,
        }

        assert normalize_margin(payload, "NFO") is None

    def test_missing_span_margin_required_key_returns_none(self) -> None:
        assert normalize_margin({}, "NFO") is None


class _RecordingMarginClient:
    """Fake BreezeClientPort capturing the exact payload sent to
    margin_calculator, so the request-shaping side of BreezeMargin is
    verified against the documented field names, not just the response
    parsing."""

    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.received_lists: list[dict[str, str]] | None = None
        self.received_exchange_code: str | None = None

    def margin_calculator(self, lists: list[dict[str, str]], exchange_code: str) -> dict[str, Any]:
        self.received_lists = lists
        self.received_exchange_code = exchange_code
        return self.response


class TestBreezeMarginCalculateMargin:
    def _success_response(self) -> dict[str, Any]:
        return {
            "Success": {
                "non_span_margin_required": "2000",
                "order_margin": "9000",
                "span_margin_required": "7000",
            },
            "Status": 200,
            "Error": None,
        }

    def test_returns_normalized_margins_from_client_response(self) -> None:
        client = _RecordingMarginClient(self._success_response())
        margin = BreezeMargin(client)
        order = OrderRequest(
            symbol="NIFTY", exchange="NFO", product_type=ProductType.OPTIONS,
            side=OrderSide.SELL, order_type=OrderType.MARKET, quantity=75,
            strike_price=Decimal("24500"), option_right=OptionRight.CALL.value,
            expiry_date="18-Aug-2026",
        )

        result = margin.calculate_margin([order], "NFO")

        assert result.span_margin == Decimal("7000")
        assert result.exposure_margin == Decimal("2000")
        assert result.total_margin == Decimal("9000")

    def test_sends_lowercased_exchange_code(self) -> None:
        client = _RecordingMarginClient(self._success_response())
        margin = BreezeMargin(client)
        order = OrderRequest(
            symbol="NIFTY", exchange="NFO", product_type=ProductType.OPTIONS,
            side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=75,
        )

        margin.calculate_margin([order], "NFO")

        assert client.received_exchange_code == "nfo"

    def test_maps_short_leg_to_sell_action_and_options_product(self) -> None:
        client = _RecordingMarginClient(self._success_response())
        margin = BreezeMargin(client)
        order = OrderRequest(
            symbol="NIFTY", exchange="NFO", product_type=ProductType.OPTIONS,
            side=OrderSide.SELL, order_type=OrderType.MARKET, quantity=75,
            strike_price=Decimal("24500"), option_right=OptionRight.PUT.value,
            expiry_date="18-Aug-2026", price=Decimal("120.5"),
        )

        margin.calculate_margin([order], "NFO")

        assert client.received_lists == [{
            "strike_price": "24500",
            "quantity": "75",
            "right": "put",
            "product": "options",
            "action": "sell",
            "price": "120.5",
            "expiry_date": "18-Aug-2026",
            "stock_code": "NIFTY",
            "cover_order_flow": "",
            "fresh_order_type": "",
            "cover_limit_rate": "",
            "cover_sltp_price": "",
            "fresh_limit_rate": "",
            "open_quantity": "",
        }]

    def test_returns_none_when_breeze_reports_no_span_margin(self) -> None:
        client = _RecordingMarginClient({
            "Success": {
                "non_span_margin_required": "0",
                "order_value": "477816.11",
                "order_margin": "0",
                "span_margin_required": None,
            },
            "Status": 200,
            "Error": None,
        })
        margin = BreezeMargin(client)
        order = OrderRequest(
            symbol="NIFTY", exchange="NFO", product_type=ProductType.OPTIONS,
            side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=195,
        )

        assert margin.calculate_margin([order], "NFO") is None

    def test_multiple_positions_are_all_included_in_the_basket(self) -> None:
        client = _RecordingMarginClient(self._success_response())
        margin = BreezeMargin(client)
        buy_leg = OrderRequest(
            symbol="NIFTY", exchange="NFO", product_type=ProductType.OPTIONS,
            side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=75,
            strike_price=Decimal("24400"), option_right=OptionRight.CALL.value,
            expiry_date="18-Aug-2026",
        )
        sell_leg = OrderRequest(
            symbol="NIFTY", exchange="NFO", product_type=ProductType.OPTIONS,
            side=OrderSide.SELL, order_type=OrderType.MARKET, quantity=75,
            strike_price=Decimal("24600"), option_right=OptionRight.CALL.value,
            expiry_date="18-Aug-2026",
        )

        margin.calculate_margin([buy_leg, sell_leg], "NFO")

        assert len(client.received_lists) == 2
        assert client.received_lists[0]["action"] == "buy"
        assert client.received_lists[1]["action"] == "sell"
