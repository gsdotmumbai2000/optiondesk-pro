"""Tests for normalize_positions(): position direction (long/short) must be
derived from Breeze's "action" field and applied as a signed quantity.

Confirmed live against a real account: Breeze reports quantity as an
always-positive magnitude ("195" for both a Buy and a Sell leg in the same
response) alongside a separate action field ("Buy"/"Sell") that the
normalizer previously discarded entirely.
"""

from decimal import Decimal

from app.brokers.breeze.normalizers.portfolio_normalizer import normalize_positions


def _response(*rows: dict) -> dict:
    return {"Success": list(rows), "Status": 200, "Error": None}


def _row(action: str, quantity: str = "195", strike: str = "25000") -> dict:
    return {
        "segment": "fno", "product_type": "Options", "exchange_code": "NFO",
        "stock_code": "NIFTY", "expiry_date": "18-Aug-2026", "strike_price": strike,
        "right": "Call", "action": action, "quantity": quantity, "average_price": "5.95",
        "ltp": "1.9", "pnl": None,
    }


class TestPositionDirectionSign:
    def test_buy_action_produces_positive_quantity(self) -> None:
        positions = normalize_positions(_response(_row("Buy")))

        assert positions[0].quantity == 195

    def test_sell_action_produces_negative_quantity(self) -> None:
        positions = normalize_positions(_response(_row("Sell")))

        assert positions[0].quantity == -195

    def test_action_is_case_insensitive(self) -> None:
        positions = normalize_positions(_response(_row("SELL")))

        assert positions[0].quantity == -195

    def test_real_bear_call_spread_response_signs_both_legs_correctly(self) -> None:
        """The exact live response shape: Buy 195x 25000 CE, Sell 195x 24700
        CE -- both report quantity="195" in the raw payload."""
        response = _response(
            _row("Buy", quantity="195", strike="25000"),
            _row("Sell", quantity="195", strike="24700"),
        )

        positions = normalize_positions(response)

        assert positions[0].strike_price == Decimal("25000")
        assert positions[0].quantity == 195
        assert positions[1].strike_price == Decimal("24700")
        assert positions[1].quantity == -195

    def test_unknown_or_missing_action_defaults_to_positive(self) -> None:
        row = _row("Buy")
        del row["action"]

        positions = normalize_positions(_response(row))

        assert positions[0].quantity == 195

    def test_other_position_fields_unaffected(self) -> None:
        positions = normalize_positions(_response(_row("Sell")))

        position = positions[0]
        assert position.symbol == "NIFTY"
        assert position.exchange == "NFO"
        assert position.average_price == Decimal("5.95")
        assert position.expiry_date == "18-Aug-2026"
        assert position.option_right == "Call"
