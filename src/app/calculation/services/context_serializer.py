"""Calculation context serializer."""

import base64
import json
from dataclasses import asdict
from typing import Any

from app.calculation.context.calculation_context import CalculationContext
from app.calculation.models.enums import ContextVersion
from app.calculation.utilities.context_decode import decode_context


class ContextSerializer:
    """Serialize and deserialize calculation contexts."""

    VERSION = ContextVersion.V1

    def to_json(self, context: CalculationContext) -> str:
        """Serialize context to JSON."""
        return json.dumps(self._encode(context), sort_keys=True)

    def from_json(self, payload: str) -> CalculationContext:
        """Deserialize context from JSON."""
        return decode_context(json.loads(payload))

    def to_binary(self, context: CalculationContext) -> bytes:
        """Serialize context to binary form."""
        encoded = self.to_json(context).encode("utf-8")
        return base64.b64encode(encoded)

    def from_binary(self, payload: bytes) -> CalculationContext:
        """Deserialize context from binary form."""
        decoded = base64.b64decode(payload).decode("utf-8")
        return self.from_json(decoded)

    def export(self, context: CalculationContext) -> dict[str, Any]:
        """Export context as dictionary."""
        return self._encode(context)

    def import_context(self, data: dict[str, Any]) -> CalculationContext:
        """Import context from dictionary."""
        return decode_context(data)

    def _encode(self, context: CalculationContext) -> dict[str, Any]:
        raw = asdict(context)
        return self._stringify(raw)

    def _stringify(self, value: Any) -> Any:
        if hasattr(value, "quantize"):
            return str(value)
        if hasattr(value, "isoformat"):
            return value.isoformat()
        if isinstance(value, dict):
            return {key: self._stringify(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._stringify(item) for item in value]
        if hasattr(value, "value"):
            return value.value
        return value
