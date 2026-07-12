"""Backtest result serialization."""

import json
from dataclasses import asdict
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any


class BacktestEncoder(json.JSONEncoder):
    """JSON encoder for backtest types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, timedelta):
            return obj.total_seconds()
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


def serialize_result(result) -> str:
    """Serialize backtest result to JSON."""
    return json.dumps(asdict(result), cls=BacktestEncoder)


def serialize_binary(result) -> bytes:
    """Serialize backtest result to bytes."""
    return serialize_result(result).encode("utf-8")
