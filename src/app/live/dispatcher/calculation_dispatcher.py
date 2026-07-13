"""Background calculation dispatcher."""

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from threading import RLock

from app.live.models.chain_key import ChainKey
from app.logging.logging_manager import get_logger

logger = get_logger(__name__)


class CalculationDispatcher:
    """Dispatch analytics jobs to a calculation thread pool."""

    def __init__(self, *, max_workers: int = 4) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="live-calc")
        self._lock = RLock()
        self._pending: set[str] = set()
        self._submitted = 0
        self._completed = 0

    @property
    def submitted_count(self) -> int:
        with self._lock:
            return self._submitted

    @property
    def completed_count(self) -> int:
        with self._lock:
            return self._completed

    def submit(self, key: ChainKey, worker: Callable[[ChainKey], None]) -> Future[None] | None:
        cache_key = key.cache_key()
        with self._lock:
            if cache_key in self._pending:
                return None
            self._pending.add(cache_key)
            self._submitted += 1
        return self._executor.submit(self._run, key, worker)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _run(self, key: ChainKey, worker: Callable[[ChainKey], None]) -> None:
        try:
            worker(key)
        except Exception as error:
            logger.warning("Live calculation failed for {key}: {error}", key=key.cache_key(), error=error)
        finally:
            with self._lock:
                self._pending.discard(key.cache_key())
                self._completed += 1
