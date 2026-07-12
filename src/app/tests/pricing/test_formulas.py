"""Pricing formula unit test skeletons."""

import pytest


@pytest.mark.skip(reason="skeleton")
def test_normal_cdf_bounds() -> None:
    """Normal CDF should remain within [0, 1]."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_normal_pdf_is_positive() -> None:
    """Normal PDF should be positive."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_discount_factor_decreases_with_time() -> None:
    """Discount factor should decline as time increases."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_forward_price_formula() -> None:
    """Forward price should follow S*exp((r-q)T)."""
    pass


@pytest.mark.skip(reason="skeleton")
def test_d1_d2_relationship() -> None:
    """d2 should equal d1 minus sigma*sqrt(T)."""
    pass
