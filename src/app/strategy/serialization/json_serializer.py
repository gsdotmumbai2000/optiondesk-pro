"""Strategy JSON serialization."""

import json
from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from app.strategy.models.enums import StrategyModelVersion
from app.strategy.models.strategy import Strategy
from app.strategy.models.template import StrategyTemplate


class StrategyEncoder(json.JSONEncoder):
    """JSON encoder for strategy types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


def serialize_strategy(strategy: Strategy) -> str:
    """Serialize strategy to JSON."""
    return json.dumps(asdict(strategy), cls=StrategyEncoder)


def serialize_template(template: StrategyTemplate) -> str:
    """Serialize template to JSON."""
    return json.dumps(asdict(template), cls=StrategyEncoder)


def deserialize_strategy(data: str) -> dict[str, Any]:
    """Deserialize strategy JSON to dict."""
    return json.loads(data)


def serialize_binary(strategy: Strategy) -> bytes:
    """Serialize strategy to UTF-8 bytes."""
    return serialize_strategy(strategy).encode("utf-8")
