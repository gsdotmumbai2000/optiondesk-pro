"""Breeze margin_calculator response normalization.

Field names (`span_margin_required`, `non_span_margin_required`,
`order_margin`) match the documented Breeze Margin Calculator API response:
https://api.icicidirect.com/breezeapi/documents/index.html
"""

from decimal import Decimal
from typing import Any

from app.brokers.breeze.utilities import to_decimal
from app.brokers.shared.models.portfolio import Margins


def normalize_margin(payload: dict[str, Any], exchange_code: str) -> Margins:
    """Convert an unwrapped margin_calculator Success payload into Margins.

    Breeze reports SPAN margin and "non-span" (exposure) margin separately;
    `order_margin` is the total margin required for the submitted basket. It
    is not split into span/exposure by Breeze, so total_margin falls back to
    span + non-span only when `order_margin` itself is missing.
    """
    span = to_decimal(payload.get("span_margin_required")) or Decimal("0")
    exposure = to_decimal(payload.get("non_span_margin_required")) or Decimal("0")
    total = to_decimal(payload.get("order_margin"))
    if total is None:
        total = span + exposure
    return Margins(
        exchange=exchange_code,
        span_margin=span,
        exposure_margin=exposure,
        additional_margin=Decimal("0"),
        total_margin=total,
    )
