"""Concurrent market data stress tests."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal

from app.market_data.cache.market_cache import MarketCache
from app.market_data.models import OHLC, Quote
from app.market_data.snapshots.snapshot_manager import SnapshotManager


def _quote(symbol: str) -> Quote:
    return Quote(
        symbol=symbol,
        exchange="NFO",
        ltp=Decimal("100"),
        ohlc=OHLC(),
        timestamp=datetime.now(timezone.utc),
    )


def test_concurrent_cache_writes() -> None:
    """Cache should handle concurrent writes."""
    cache = MarketCache()
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(cache.put_quote, _quote(f"S{i}")) for i in range(200)]
        for future in futures:
            future.result()
    assert cache.quote_count == 200


def test_concurrent_snapshots() -> None:
    """Snapshot manager should be thread-safe."""
    manager = SnapshotManager()

    def capture() -> None:
        manager.capture({f"K{i}": _quote("NIFTY") for i in range(5)})

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(capture) for _ in range(20)]
        for future in futures:
            future.result()
    assert manager.current is not None
