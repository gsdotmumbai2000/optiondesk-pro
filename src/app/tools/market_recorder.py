#!/usr/bin/env python3
"""
Market data recorder for live NIFTY ticks.

Standalone CLI wrapper around the app's own TickRecorder (see
app.simulator.recorder.tick_recorder), which is normally only started
in-process via RECORD_MARKET_DATA=1. Writes to the same
<data_directory>/simulator/recordings/nifty_YYYYMMDD.jsonl location the
simulator broker and ReplayEngine already read from, so a recording made
with this tool can be replayed in simulator mode with no manual copy step.
"""

import sys
import time
from pathlib import Path

from app.logging.logging_manager import get_logger
from app.simulator.recorder.tick_recorder import TickRecorder

logger = get_logger(__name__)


def _connect_broker(broker_provider) -> None:
    """Log in and connect the broker so ticks start flowing.

    ApplicationKernel.initialize() only builds the broker provider; it never
    connects it. Normally that happens in DesktopApplication.run()/.show()
    via _restore_broker_session() + _activate_simulator_broker() (see
    src/app/ui/application/desktop_app.py), which only run once the UI
    exists. This tool has no UI, so it must trigger the connect itself --
    otherwise SubscriptionService's default NIFTY watchlist (queued during
    kernel bootstrap) never activates and no ticks are ever published.

    Uses BrokerProvider.manager.connect() rather than broker.connect()
    directly: with auto_login enabled, broker.connect() alone only flips
    state to AUTHENTICATING and returns -- BrokerManager._connect_once()
    is what actually calls broker.authenticate() (real login + websocket
    connect + BrokerConnectedEvent) afterward. This is the same call
    _activate_simulator_broker() and BrokerWorkspaceService.login() use.
    """
    if broker_provider is None:
        return
    try:
        broker_provider.manager.connect()
        logger.info("Broker connected: {code}", code=broker_provider.broker.broker_code)
    except Exception:
        logger.error("Broker connect failed; no live ticks will be recorded", exc_info=True)


def main() -> int:
    """Main entry point for the market recorder application."""
    try:
        # Import required components lazily to avoid circular imports
        from app.kernel.application_kernel import ApplicationKernel

        # Initialize the application kernel (without starting it fully)
        kernel = ApplicationKernel()
        kernel.initialize()

        # Same location SimulatorBroker/ReplayEngine/MarketModeService read
        # recordings from -- see application_kernel.py::_bootstrap_tick_recorder
        assert kernel.configuration_manager is not None
        data_dir = Path(kernel.configuration_manager.configuration.application.data_directory)
        recordings_dir = data_dir / "simulator" / "recordings"

        recorder = TickRecorder(kernel.event_bus, recordings_dir)

        # Subscribe before connecting the broker so no early ticks are missed
        recorder.start()

        # initialize() alone never logs the broker in (see _connect_broker docstring)
        _connect_broker(kernel.broker_provider)

        logger.info("Market recorder is now running - press Ctrl+C to stop")

        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down market recorder...")
            kernel.shutdown()
            return 0

    except Exception as error:
        logger.error(f"Failed to start market recorder: {error}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
