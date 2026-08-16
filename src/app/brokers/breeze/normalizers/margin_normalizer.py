"""Breeze margin_calculator response normalization.

Field names (`span_margin_required`, `non_span_margin_required`,
`order_margin`) match the documented Breeze Margin Calculator API response:
https://api.icicidirect.com/breezeapi/documents/index.html
"""

from decimal import Decimal
from typing import Any

from app.brokers.breeze.utilities import to_decimal
from app.brokers.shared.models.portfolio import Margins


def normalize_margin(payload: dict[str, Any], exchange_code: str) -> Margins | None:
    """Convert an unwrapped margin_calculator Success payload into Margins,
    or None when Breeze didn't actually compute a margin.

    Breeze reports SPAN margin and "non-span" (exposure) margin separately;
    `order_margin` is the total margin required for the submitted basket. It
    is not split into span/exposure by Breeze, so total_margin falls back to
    span + non-span only when `order_margin` itself is missing.

    Confirmed live against a real account on a non-trading day: Breeze
    returned `span_margin_required: null` (with `order_margin: "0"`, not
    null) while still computing a real, non-zero `order_value` for the same
    request -- i.e. the request was accepted and understood, but no SPAN
    parameters were available to price it. A null span is never a
    legitimate "zero margin" answer for a real position, so treat it as
    "unavailable" and return None rather than a confident-looking zero,
    which callers would otherwise display as this position needing no
    margin at all.
    """
    if payload.get("span_margin_required") is None:
        return None
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
