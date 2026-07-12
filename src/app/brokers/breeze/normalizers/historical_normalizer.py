"""Normalize Breeze historical data responses."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from app.brokers.breeze.utilities import to_decimal, to_int
from app.brokers.shared.models import HistoricalBar


def normalize_historical(payload: Any) -> list[HistoricalBar]:
    """Convert Breeze historical payload to bars."""
    rows = payload if isinstance(payload, list) else []
    bars: list[HistoricalBar] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        timestamp = _parse_datetime(row.get("datetime") or row.get("date_time"))
        bars.append(
            HistoricalBar(
                timestamp=timestamp,
                open=to_decimal(row.get("open")) or Decimal("0"),
                high=to_decimal(row.get("high")) or Decimal("0"),
                low=to_decimal(row.get("low")) or Decimal("0"),
                close=to_decimal(row.get("close")) or Decimal("0"),
                volume=to_int(row.get("volume")) or 0,
                open_interest=to_int(row.get("open_interest")),
            )
        )
    return bars


def _parse_datetime(value: Any) -> datetime:
    """Parse Breeze datetime string."""
    text = str(value or "")
    for fmt in ("%d-%b-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d-%b-%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return datetime.now()
