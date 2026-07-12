"""Market data file loader."""

import json
from pathlib import Path
from typing import Any

import yaml


class MarketDataLoader:
    """Load market master seed data from YAML or JSON files."""

    def load_yaml(self, path: Path) -> list[dict[str, Any]]:
        """Load a list of records from YAML."""
        if not path.exists():
            return []
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return self._extract_records(data)

    def load_json(self, path: Path) -> list[dict[str, Any]]:
        """Load a list of records from JSON."""
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return self._extract_records(data)

    def load_records(self, path: Path) -> list[dict[str, Any]]:
        """Load records based on file extension."""
        if path.suffix.lower() in {".yaml", ".yml"}:
            return self.load_yaml(path)
        if path.suffix.lower() == ".json":
            return self.load_json(path)
        return []

    @staticmethod
    def _extract_records(data: Any) -> list[dict[str, Any]]:
        """Normalize loaded data into a list of record dictionaries."""
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            for key in ("instruments", "underlyings", "holidays", "sessions", "items"):
                value = data.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
        return []
