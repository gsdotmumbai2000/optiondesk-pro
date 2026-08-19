"""Tests for MarketViewModel option-chain row building and table rendering."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.ui.option_chain.chain_model import COLUMNS, OptionChainTableModel
from app.ui.viewmodels.market_viewmodel import MarketViewModel


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Provide a Qt application instance for widget/model tests."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _strike(price: str = "24500", **overrides) -> dict:
    row = {
        "strike_price": price,
        "call_symbol": "NIFTY24500CE",
        "put_symbol": "NIFTY24500PE",
        "call_oi": 45000,
        "put_oi": 38000,
        "call_volume": 98000,
        "put_volume": 76000,
        "call_iv": None,
        "put_iv": None,
        "is_atm": False,
    }
    row.update(overrides)
    return row


class TestRestStrikeRowBuilding:
    """MarketViewModel._rows_from_rest_strikes renders CE and PE rows."""

    def test_one_strike_produces_ce_and_pe_rows(self) -> None:
        rows = MarketViewModel._rows_from_rest_strikes([_strike()])

        assert len(rows) == 2
        assert rows[0][0] == "CE"
        assert rows[1][0] == "PE"

    def test_strike_oi_and_volume_populate_from_domain_chain(self) -> None:
        rows = MarketViewModel._rows_from_rest_strikes([_strike()])

        call_row, put_row = rows
        assert call_row[1] == "24500"
        assert call_row[3] == "45000"
        assert call_row[4] == "98000"
        assert put_row[3] == "38000"
        assert put_row[4] == "76000"

    def test_missing_iv_and_greeks_render_as_placeholder(self) -> None:
        rows = MarketViewModel._rows_from_rest_strikes([_strike()])

        call_row = rows[0]
        assert call_row[5] == "—"  # IV: not calculated in this phase
        assert call_row[6:] == ("—", "—", "—", "—")  # Delta, Gamma, Theta, Vega

    def test_no_greeks_are_invented_when_iv_is_present(self) -> None:
        """Even if IV is available, Gamma/Theta/Vega must still be '—' (later phase)."""
        rows = MarketViewModel._rows_from_rest_strikes([_strike(call_iv="14.2")])

        call_row = rows[0]
        assert call_row[5] == "14.20"
        assert call_row[6:] == ("—", "—", "—", "—")

    def test_multiple_strikes_produce_rows_in_order(self) -> None:
        rows = MarketViewModel._rows_from_rest_strikes([_strike("24500"), _strike("24600")])

        assert [row[1] for row in rows] == ["24500", "24500", "24600", "24600"]


class TestIvAndGreeksAreRoundedToTwoDecimalPlaces:
    """IV and Delta/Gamma/Theta/Vega all render rounded to 2 decimal places
    in the option chain table -- full precision is only needed for
    calculations, not for a strike-by-strike glance table."""

    def test_rest_strike_iv_and_greeks_are_rounded(self) -> None:
        rows = MarketViewModel._rows_from_rest_strikes([
            _strike(
                call_iv="18.567891", call_delta="0.4023156", call_gamma="0.0012345",
                call_theta="-1.5678", call_vega="12.3456",
            ),
        ])

        call_row = rows[0]
        assert call_row[5] == "18.57"
        assert call_row[6:] == ("0.40", "0.00", "-1.57", "12.35")

    def test_live_chain_iv_and_greeks_are_rounded(self) -> None:
        chain = {
            "strikes": {
                "24500": {
                    "strike_price": "24500",
                    "call": {
                        "implied_volatility": "18.567891", "delta": "0.4023156",
                        "gamma": "0.0012345", "theta": "-1.5678", "vega": "12.3456",
                    },
                    "put": {},
                },
            },
        }

        rows = MarketViewModel._rows_from_live_chain(chain)

        call_row = rows[0]
        assert call_row[5] == "18.57"
        assert call_row[6:] == ("0.40", "0.00", "-1.57", "12.35")

    def test_missing_iv_and_greeks_still_render_as_placeholder(self) -> None:
        rows = MarketViewModel._rows_from_rest_strikes([_strike()])

        assert rows[0][5] == "—"
        assert rows[0][6:] == ("—", "—", "—", "—")

    def test_non_numeric_iv_or_greek_renders_as_placeholder_not_a_crash(self) -> None:
        rows = MarketViewModel._rows_from_rest_strikes([_strike(call_iv="n/a", call_delta="n/a")])

        assert rows[0][5] == "—"
        assert rows[0][6] == "—"


class TestOptionChainTableModelRendering:
    """The existing OptionChainTableModel renders CE/PE rows unchanged."""

    def test_table_model_displays_ce_and_pe_rows(self, qapp: QApplication) -> None:
        model = OptionChainTableModel()
        rows = MarketViewModel._rows_from_rest_strikes([_strike()])

        model.set_placeholder_rows(rows)

        assert model.rowCount() == 2
        assert model.columnCount() == len(COLUMNS)
        assert model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole) == "CE"
        assert model.data(model.index(1, 0), Qt.ItemDataRole.DisplayRole) == "PE"
        assert model.data(model.index(0, 1), Qt.ItemDataRole.DisplayRole) == "24500"
