"""Market data loader tests."""

import json
from pathlib import Path

import yaml

from app.market.repositories.data_loader import MarketDataLoader


def test_load_yaml_list(tmp_path: Path) -> None:
    """YAML list files should load directly."""
    path = tmp_path / "items.yaml"
    path.write_text(yaml.dump([{"symbol": "NIFTY"}]), encoding="utf-8")
    records = MarketDataLoader().load_yaml(path)
    assert records == [{"symbol": "NIFTY"}]


def test_load_yaml_wrapped_dict(tmp_path: Path) -> None:
    """YAML dict wrappers should extract list keys."""
    path = tmp_path / "underlyings.yaml"
    path.write_text(
        yaml.dump({"underlyings": [{"symbol": "BANKNIFTY"}]}),
        encoding="utf-8",
    )
    records = MarketDataLoader().load_yaml(path)
    assert records == [{"symbol": "BANKNIFTY"}]


def test_load_json_wrapped_dict(tmp_path: Path) -> None:
    """JSON dict wrappers should extract list keys."""
    path = tmp_path / "holidays.json"
    path.write_text(
        json.dumps({"holidays": [{"exchange": "NSE"}]}),
        encoding="utf-8",
    )
    records = MarketDataLoader().load_json(path)
    assert records == [{"exchange": "NSE"}]


def test_load_records_by_extension(tmp_path: Path) -> None:
    """load_records should route by file extension."""
    yaml_path = tmp_path / "sessions.yml"
    yaml_path.write_text(yaml.dump([{"exchange": "NSE"}]), encoding="utf-8")
    assert MarketDataLoader().load_records(yaml_path) == [{"exchange": "NSE"}]

    unknown = tmp_path / "data.txt"
    unknown.write_text("ignored", encoding="utf-8")
    assert MarketDataLoader().load_records(unknown) == []


def test_missing_file_returns_empty(tmp_path: Path) -> None:
    """Missing files should return empty lists."""
    loader = MarketDataLoader()
    missing = tmp_path / "missing.yaml"
    assert loader.load_yaml(missing) == []
    assert loader.load_json(missing) == []
