"""Expiry manager tests."""

from datetime import date, datetime, time

from app.market.bootstrap import MarketMasterProvider
from app.market.enums import ExpiryType


def test_generate_weekly_expiries(market_provider: MarketMasterProvider) -> None:
    """Weekly expiries should be generated for NIFTY."""
    manager = market_provider.cache.expiry_manager
    records = manager.generate_expiries(
        "NIFTY",
        "NSEFO",
        from_date=date(2026, 7, 1),
        to_date=date(2026, 8, 31),
        expiry_type=ExpiryType.WEEKLY,
    )
    assert len(records) >= 4
    assert all(item.expiry_date.weekday() == 1 for item in records)


def test_holiday_shift_moves_to_previous_trading_day(
    market_provider: MarketMasterProvider,
) -> None:
    """Expiry on a holiday should shift to the previous trading day."""
    manager = market_provider.cache.holiday_manager
    shifted = manager.shift_for_holiday("NSE", date(2026, 1, 26))
    assert shifted == date(2026, 1, 23)


def test_calculate_dte(market_provider: MarketMasterProvider) -> None:
    """DTE should count trading days only."""
    manager = market_provider.cache.expiry_manager
    dte = manager.calculate_dte("NSEFO", date(2026, 7, 6), date(2026, 7, 14))
    assert dte > 0


def test_calculate_tte(market_provider: MarketMasterProvider) -> None:
    """TTE should return positive seconds before expiry close."""
    manager = market_provider.cache.expiry_manager
    now = datetime(2026, 7, 6, 10, 0, 0)
    tte = manager.calculate_tte(
        "NSEFO", now, date(2026, 7, 14), market_close=time(15, 30)
    )
    assert tte > 0


def test_monthly_expiry_last_weekday(market_provider: MarketMasterProvider) -> None:
    """Monthly expiry should fall on last configured weekday."""
    manager = market_provider.cache.expiry_manager
    records = manager.generate_expiries(
        "NIFTY",
        "NSEFO",
        from_date=date(2026, 7, 1),
        to_date=date(2026, 7, 31),
        expiry_type=ExpiryType.MONTHLY,
    )
    assert len(records) == 1
    assert records[0].expiry_date.month == 7
