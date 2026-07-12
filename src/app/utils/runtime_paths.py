"""Resolve application paths for development and frozen (PyInstaller) runs."""

import sys
from pathlib import Path


def is_frozen() -> bool:
    """Return whether the app runs from a PyInstaller bundle."""
    return bool(getattr(sys, "frozen", False))


def application_root() -> Path:
    """Return install directory (folder containing the executable when frozen)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def bundle_root() -> Path:
    """Return directory containing bundled read-only assets."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", application_root()))
    return application_root()
