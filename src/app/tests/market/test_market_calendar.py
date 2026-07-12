"""Market calendar tests."""

from datetime import date, datetime, time

from app.market.bootstrap import MarketMasterProvider


def test_market_open_close_times(market_provider: MarketMasterProvider) -> None:
    """Regular session times should be available."""
    calendar = market_provider.cache.market_calendar
    assert calendar.market_open("NSEFO") == time(9, 15)
    assert calendar.market_close("NSEFO") == time(15, 30)


def test_pre_and_post_close_windows(market_provider: MarketMasterProvider) -> None:
    """Pre-open and post-close windows should be configured."""
    calendar = market_provider.cache.market_calendar
    pre_open = calendar.pre_open_window("NSEFO")
    post_close = calendar.post_close_window("NSEFO")
    assert pre_open is not None
    assert post_close is not None


def test_is_market_open_during_regular_session(
    market_provider: MarketMasterProvider,
) -> None:
    """Market should be open during regular hours on trading day."""
    service = market_provider.calendar_service
    moment = datetime(2026, 7, 6, 10, 30, 0)
    assert service.is_market_open("NSEFO", moment) is True


def test_is_market_closed_on_weekend(market_provider: MarketMasterProvider) -> None:
    """Market should be closed on weekends."""
    service = market_provider.calendar_service
    assert service.is_trading_day("NSEFO", date(2026, 7, 11)) is False
