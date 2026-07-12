"""Trading session service tests."""

from app.market.bootstrap import MarketMasterProvider
from app.market.enums import SessionType


def test_get_regular_session(market_provider: MarketMasterProvider) -> None:
    """Regular session should be returned for NSEFO."""
    session = market_provider.session_service.get_regular_session("NSEFO")
    assert session is not None
    assert session.session_type == SessionType.REGULAR


def test_get_all_sessions(market_provider: MarketMasterProvider) -> None:
    """All configured sessions should be returned."""
    sessions = market_provider.session_service.get_sessions("NSEFO")
    assert len(sessions) >= 3
