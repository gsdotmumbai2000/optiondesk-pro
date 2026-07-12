"""Query models."""

from dataclasses import dataclass, field
from typing import Any

from app.application.models.enums import QueryType


@dataclass(frozen=True, slots=True)
class ApplicationQuery:
    """Base application query."""

    query_type: QueryType
    session_id: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class QueryResult:
    """Generic query result wrapper."""

    query_type: QueryType
    success: bool
    data: Any = None
    error: str = ""
