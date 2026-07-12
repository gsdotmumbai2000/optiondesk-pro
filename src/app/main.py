"""OptionDesk Pro entry point."""

import sys
from pathlib import Path

from app.kernel.application_kernel import ApplicationKernel
from app.utils.constants import CONFIG_DIR


def main() -> int:
    """Application entry point."""
    config_dir = Path(CONFIG_DIR)
    kernel = ApplicationKernel(config_dir=config_dir if config_dir.exists() else None)
    exit_code = 0
    try:
        kernel.initialize()
        exit_code = kernel.start()
    finally:
        kernel.shutdown()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
