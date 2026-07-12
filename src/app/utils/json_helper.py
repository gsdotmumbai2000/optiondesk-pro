"""JSON serialization utilities."""

import json
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class JsonHelper:
    """Helper for JSON encoding and decoding."""

    @staticmethod
    def dumps(data: Any, indent: int | None = None) -> str:
        """Serialize data to a JSON string."""
        return json.dumps(data, indent=indent, default=JsonHelper._default_encoder)

    @staticmethod
    def loads(value: str) -> Any:
        """Deserialize a JSON string."""
        return json.loads(value)

    @staticmethod
    def model_to_dict(model: BaseModel) -> dict[str, Any]:
        """Convert a Pydantic model to a dictionary."""
        return model.model_dump(mode="json")

    @staticmethod
    def model_from_dict(model_type: type[T], data: dict[str, Any]) -> T:
        """Create a Pydantic model from a dictionary."""
        return model_type.model_validate(data)

    @staticmethod
    def _default_encoder(value: Any) -> Any:
        """Encode unsupported types for JSON serialization."""
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")
