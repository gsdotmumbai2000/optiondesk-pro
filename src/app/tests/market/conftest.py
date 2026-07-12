"""Market Master test fixtures."""

from pathlib import Path

import pytest

from app.events.event_bus import EventBus
from app.market.bootstrap import MarketMasterProvider


@pytest.fixture
def market_provider(tmp_path: Path) -> MarketMasterProvider:
    """Create a market master provider for tests."""
    provider = MarketMasterProvider(tmp_path, EventBus())
    yield provider
    provider.shutdown()
