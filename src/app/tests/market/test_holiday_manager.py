"""Holiday manager tests."""

from datetime import date

from app.market.bootstrap import MarketMasterProvider


def test_weekend_is_not_trading_day(market_provider: MarketMasterProvider) -> None:
    """Weekends should not be trading days."""
    manager = market_provider.cache.holiday_manager
    assert manager.is_trading_day("NSE", date(2026, 7, 11)) is False


def test_republic_day_holiday(market_provider: MarketMasterProvider) -> None:
    """Republic Day should be a holiday."""
    manager = market_provider.cache.holiday_manager
    assert manager.is_trading_holiday("NSE", date(2026, 1, 26)) is True
    assert manager.is_trading_day("NSE", date(2026, 1, 26)) is False


def test_next_trading_day(market_provider: MarketMasterProvider) -> None:
    """Next trading day should skip weekend."""
    manager = market_provider.cache.holiday_manager
    next_day = manager.next_trading_day("NSE", date(2026, 7, 10))
    assert next_day == date(2026, 7, 13)


def test_holiday_service(market_provider: MarketMasterProvider) -> None:
    """Holiday service should expose holidays."""
    holidays = market_provider.holiday_service.get_holidays("NSE")
    assert any(item.holiday_name == "Republic Day" for item in holidays)
