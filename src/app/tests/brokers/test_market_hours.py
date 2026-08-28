"""Tests for AUTO mode's IST market-hours broker resolution."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.brokers.shared.enums import BrokerCode
from app.brokers.shared.market_hours import (is_within_live_window,
                                              resolve_effective_broker_code)
from app.config.models.app_config import MarketMode

IST = ZoneInfo("Asia/Kolkata")


def _ist(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=IST)


class TestIsWithinLiveWindow:
    def test_mid_session_weekday_is_within_window(self) -> None:
        assert is_within_live_window(_ist(2026, 8, 24, 11, 0)) is True  # Monday

    def test_before_nine_am_is_outside_window(self) -> None:
        assert is_within_live_window(_ist(2026, 8, 24, 8, 59)) is False

    def test_after_three_forty_pm_is_outside_window(self) -> None:
        assert is_within_live_window(_ist(2026, 8, 24, 15, 41)) is False

    def test_window_boundaries_are_inclusive(self) -> None:
        assert is_within_live_window(_ist(2026, 8, 24, 9, 0)) is True
        assert is_within_live_window(_ist(2026, 8, 24, 15, 40)) is True

    def test_saturday_is_outside_window(self) -> None:
        assert is_within_live_window(_ist(2026, 8, 22, 11, 0)) is False  # Saturday

    def test_sunday_is_outside_window(self) -> None:
        assert is_within_live_window(_ist(2026, 8, 23, 11, 0)) is False  # Sunday


class TestResolveEffectiveBrokerCode:
    def test_live_mode_always_returns_live_broker(self) -> None:
        code = resolve_effective_broker_code(
            MarketMode.LIVE, "BREEZE", now=_ist(2026, 8, 22, 3, 0)
        )
        assert code == "BREEZE"

    def test_simulator_mode_always_returns_simulator(self) -> None:
        code = resolve_effective_broker_code(
            MarketMode.SIMULATOR, "BREEZE", now=_ist(2026, 8, 24, 11, 0)
        )
        assert code == BrokerCode.SIMULATOR.value

    def test_auto_mode_during_market_hours_returns_live_broker(self) -> None:
        code = resolve_effective_broker_code(
            MarketMode.AUTO, "BREEZE", now=_ist(2026, 8, 24, 11, 0)
        )
        assert code == "BREEZE"

    def test_auto_mode_outside_market_hours_returns_simulator(self) -> None:
        code = resolve_effective_broker_code(
            MarketMode.AUTO, "BREEZE", now=_ist(2026, 8, 24, 20, 0)
        )
        assert code == BrokerCode.SIMULATOR.value

    def test_auto_mode_on_weekend_returns_simulator(self) -> None:
        code = resolve_effective_broker_code(
            MarketMode.AUTO, "BREEZE", now=_ist(2026, 8, 22, 11, 0)
        )
        assert code == BrokerCode.SIMULATOR.value
