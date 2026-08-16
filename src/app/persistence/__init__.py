"""Persistence layer package.

Generic dataclass<->JSON codec (dataclass_codec.py) used by the real
SQLite-backed repositories in strategy/, portfolio/, and backtesting/.
"""

from app.persistence.dataclass_codec import from_json, to_json

__all__: list[str] = ["from_json", "to_json"]
