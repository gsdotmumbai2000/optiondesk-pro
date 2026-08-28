"""Coordinate runtime Live <-> Simulator market-mode switching.

Owns the one ReplayEngine that may exist at a time: simulated ticks are
pushed straight into the shared EventDispatcher on a background thread
independent of broker connection state (see ReplayEngine), so starting a
second one while an old one is still running would double-feed the
dispatcher. This service must therefore be constructed exactly once for
the app's lifetime and reused for every switch, rather than rebuilt per
call.
"""

from pathlib import Path

from app.brokers.bootstrap import BrokerProvider
from app.brokers.shared.enums import BrokerCode
from app.brokers.shared.market_hours import resolve_effective_broker_code
from app.config.configuration_manager import ConfigurationManager
from app.config.models.app_config import BrokerConfig, MarketMode
from app.logging.logging_manager import get_logger
from app.market_data.bootstrap import MarketDataProvider
from app.simulator.player.replay_engine import ReplayEngine, find_latest_recording

logger = get_logger(__name__)


class MarketModeService:
    """Switch the active broker between the configured live broker and the
    simulator, either explicitly or via AUTO's IST market-hours check."""

    def __init__(
        self,
        broker_provider: BrokerProvider,
        market_data: MarketDataProvider,
        broker_config: BrokerConfig,
        data_directory: Path,
        configuration_manager: ConfigurationManager | None = None,
    ) -> None:
        """Initialize service."""
        self._broker_provider = broker_provider
        self._market_data = market_data
        self._config = broker_config
        self._configuration_manager = configuration_manager
        self._recordings_dir = data_directory / "simulator" / "recordings"
        self._replay_engine: ReplayEngine | None = None

    @property
    def mode(self) -> MarketMode:
        """Return the configured mode (auto/live/simulator)."""
        return self._config.market_mode

    @property
    def active_broker_code(self) -> str:
        """Return the broker code actually active right now."""
        return self._broker_provider.manager.broker_code

    def initialize(self) -> None:
        """Start the replay engine if the app booted straight into simulator
        mode. Does not touch broker connection -- that remains the caller's
        responsibility (see DesktopApplication._activate_simulator_broker)."""
        if self.active_broker_code == BrokerCode.SIMULATOR.value:
            self._start_replay()

    def apply(self, mode: MarketMode) -> str:
        """Switch to `mode`, hot-swapping the broker if the effective code
        changed, and persisting the choice. Returns the effective broker
        code now active. Propagates BrokerConnectionException on a failed
        live connect attempt (mode is still persisted as requested)."""
        effective_code = resolve_effective_broker_code(mode, self._config.broker_code)
        self._config.market_mode = mode
        if self._configuration_manager is not None:
            self._configuration_manager.save()
        if effective_code == self.active_broker_code:
            return effective_code
        if effective_code != BrokerCode.SIMULATOR.value:
            self._stop_replay()
        self._broker_provider.manager.switch_to(effective_code)
        if effective_code == BrokerCode.SIMULATOR.value:
            self._start_replay()
        return effective_code

    def stop(self) -> None:
        """Stop the replay engine, if running."""
        self._stop_replay()

    def _start_replay(self) -> None:
        self._stop_replay()
        recording_path = find_latest_recording(self._recordings_dir)
        if recording_path is None:
            logger.warning(
                "Simulator mode selected but no recordings found in {dir}; "
                "run with RECORD_MARKET_DATA=1 against the real broker during "
                "market hours first",
                dir=self._recordings_dir,
            )
            return
        self._replay_engine = ReplayEngine(self._market_data.dispatcher, recording_path)
        self._replay_engine.start()

    def _stop_replay(self) -> None:
        if self._replay_engine is not None:
            self._replay_engine.stop()
            self._replay_engine = None
