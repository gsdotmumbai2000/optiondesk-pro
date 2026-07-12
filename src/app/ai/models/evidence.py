"""Supporting evidence models."""

from dataclasses import dataclass
from decimal import Decimal

from app.ai.models.enums import EvidenceSource


@dataclass(frozen=True, slots=True)
class EvidenceMetric:
    """Single traceable metric from an engine."""

    source: EvidenceSource
    metric_name: str
    metric_value: str
    engine_reference: str


@dataclass(frozen=True, slots=True)
class SupportingEvidence:
    """Evidence bundle backing a recommendation."""

    evidence_id: str
    summary: str
    metrics: tuple[EvidenceMetric, ...]
    affected_metrics: tuple[str, ...]
