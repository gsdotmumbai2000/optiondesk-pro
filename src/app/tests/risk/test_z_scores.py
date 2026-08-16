"""Tests for z_score(): VaR confidence-level lookup."""

from decimal import Decimal

from app.risk.analytics.z_scores import z_score
from app.risk.models.enums import ConfidenceLevel


class TestZScoreLookup:
    def test_p95_matches_standard_one_tailed_z_value(self) -> None:
        assert z_score(ConfidenceLevel.P95) == Decimal("1.645")

    def test_p99_matches_standard_one_tailed_z_value(self) -> None:
        assert z_score(ConfidenceLevel.P99) == Decimal("2.326")

    def test_p99_z_score_is_larger_than_p95(self) -> None:
        assert z_score(ConfidenceLevel.P99) > z_score(ConfidenceLevel.P95)
