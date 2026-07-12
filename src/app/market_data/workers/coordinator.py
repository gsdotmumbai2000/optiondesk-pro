"""Market data worker coordinator."""

from app.market_data.workers.worker_pool import WorkerPool


class MarketDataWorkers:
    """Coordinate background workers for market data."""

    def __init__(self) -> None:
        """Initialize worker pools."""
        self.quotes = WorkerPool("md-quotes", workers=2)
        self.option_chain = WorkerPool("md-chain", workers=1)
        self.historical = WorkerPool("md-historical", workers=1)
        self.snapshot = WorkerPool("md-snapshot", workers=1)
        self.cleanup = WorkerPool("md-cleanup", workers=1)

    def start(self) -> None:
        """Start all workers."""
        self.quotes.start()
        self.option_chain.start()
        self.historical.start()
        self.snapshot.start()
        self.cleanup.start()

    def stop(self) -> None:
        """Stop all workers."""
        self.quotes.stop()
        self.option_chain.stop()
        self.historical.stop()
        self.snapshot.stop()
        self.cleanup.stop()
