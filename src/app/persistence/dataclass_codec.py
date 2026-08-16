"""Generic JSON codec for the frozen dataclasses used as domain models
across this codebase (Strategy, Portfolio, BacktestResult, and their
nested models).

Handles exactly the type vocabulary those models use: nested dataclasses
(recursed via typing.get_type_hints, so it also works under
`from __future__ import annotations`), Enum, Decimal, date, datetime,
timedelta, `tuple[T, ...]`, `T | None`, and plain JSON primitives.

Not a general-purpose serializer -- there is no schema versioning or
graceful handling of missing/extra fields. It is only used to round-trip
objects this codebase itself encoded, via to_json()/from_json() for the
same dataclass type.
"""

import dataclasses
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints


def to_json(obj: Any) -> str:
    """Serialize a dataclass instance (or primitive) to a JSON string."""
    return json.dumps(_encode(obj))


def from_json(cls: type, data: str) -> Any:
    """Deserialize a JSON string back into an instance of `cls`."""
    return _decode(cls, json.loads(data))


def _encode(value: Any) -> Any:
    if value is None:
        return None
    if dataclasses.is_dataclass(value):
        return {f.name: _encode(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, (tuple, list)):
        return [_encode(item) for item in value]
    if isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"dataclass_codec cannot encode value of type {type(value)!r}")


def _decode(annotation: Any, value: Any) -> Any:
    if value is None:
        return None
    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        non_none_args = [arg for arg in get_args(annotation) if arg is not type(None)]
        return _decode(non_none_args[0], value)
    if origin is tuple:
        item_type = get_args(annotation)[0]
        return tuple(_decode(item_type, item) for item in value)
    if dataclasses.is_dataclass(annotation):
        hints = get_type_hints(annotation)
        kwargs = {name: _decode(hints[name], value.get(name)) for name in hints}
        return annotation(**kwargs)
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return annotation(value)
    if annotation is Decimal:
        return Decimal(value)
    if annotation is datetime:
        return datetime.fromisoformat(value)
    if annotation is date:
        return date.fromisoformat(value)
    if annotation is timedelta:
        return timedelta(seconds=value)
    return value
