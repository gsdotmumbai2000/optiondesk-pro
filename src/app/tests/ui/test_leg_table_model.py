"""Tests for StrategyLegTableModel: the Strategy Builder's pending-leg
table, mirroring test_strategy_list_view.py's StrategyListTableModel tests.
"""

from datetime import date
from decimal import Decimal

import pytest
from PySide6.QtWidgets import QApplication

from app.strategy.models.enums import LegKind
from app.strategy.models.leg import StrategyLeg
from app.ui.strategy.leg_table_model import COLUMNS, StrategyLegTableModel


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _leg(**overrides) -> StrategyLeg:
    defaults = dict(
        leg_id="leg-1", kind=LegKind.CALL_BUY, quantity=2, premium=Decimal("120.5"),
        strike=Decimal("24500"), underlying="NIFTY", exchange="NFO",
        expiry=date(2026, 8, 18), multiplier=75,
    )
    defaults.update(overrides)
    return StrategyLeg(**defaults)


class TestStrategyLegTableModel:
    def test_renders_side_right_strike_expiry_qty_premium(self, qapp: QApplication) -> None:
        model = StrategyLegTableModel()

        model.set_legs([_leg()])

        assert model.rowCount() == 1
        assert model.columnCount() == len(COLUMNS)
        assert model.data(model.index(0, 0)) == "Buy"
        assert model.data(model.index(0, 1)) == "CE"
        assert model.data(model.index(0, 2)) == "24500"
        assert model.data(model.index(0, 3)) == "2026-08-18"
        assert model.data(model.index(0, 4)) == "2"
        assert model.data(model.index(0, 5)) == "120.5"

    def test_sell_and_put_render_correctly(self, qapp: QApplication) -> None:
        model = StrategyLegTableModel()

        model.set_legs([_leg(kind=LegKind.PUT_SELL)])

        assert model.data(model.index(0, 0)) == "Sell"
        assert model.data(model.index(0, 1)) == "PE"

    def test_missing_expiry_renders_placeholder(self, qapp: QApplication) -> None:
        model = StrategyLegTableModel()

        model.set_legs([_leg(expiry=None)])

        assert model.data(model.index(0, 3)) == "—"

    def test_maps_row_back_to_leg_id(self, qapp: QApplication) -> None:
        model = StrategyLegTableModel()

        model.set_legs([_leg(leg_id="leg-1"), _leg(leg_id="leg-2")])

        assert model.leg_id_for_row(0) == "leg-1"
        assert model.leg_id_for_row(1) == "leg-2"

    def test_out_of_range_row_returns_empty_string(self, qapp: QApplication) -> None:
        model = StrategyLegTableModel()
        model.set_legs([_leg()])

        assert model.leg_id_for_row(5) == ""
