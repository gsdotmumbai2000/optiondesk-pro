"""Margin optimization package."""

from app.margin.optimization.margin_optimizer import MarginOptimizer
from app.margin.optimization.suggestions import generate_suggestions

__all__ = ["MarginOptimizer", "generate_suggestions"]
