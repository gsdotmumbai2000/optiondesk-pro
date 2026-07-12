"""Margin domain models."""

from app.margin.models.broker_response import BrokerMarginResponse
from app.margin.models.enums import MarginModelVersion, MarginSource
from app.margin.models.optimization import (
    MarginOptimizationResult,
    MarginReductionSuggestion,
)
from app.margin.models.request import MarginAnalysisRequest
from app.margin.models.result import MarginResult

__all__ = [
    "BrokerMarginResponse",
    "MarginAnalysisRequest",
    "MarginModelVersion",
    "MarginOptimizationResult",
    "MarginReductionSuggestion",
    "MarginResult",
    "MarginSource",
]
