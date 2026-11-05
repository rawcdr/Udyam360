"""Unit tests for Pricing Engine."""

import pytest
from app.schemas.business_profile import BusinessProfile
from app.services.pricing_engine import pricing_engine


def test_single_product_pricing_range():
    """Verify minimum, maximum monthly charges and setup fee for Biz Fibre 100."""
    calc = pricing_engine.calculate_price(["P01"])
    # P01: 999 to 1199, setup 0
    assert calc.monthly_total_min == 999.0
    assert calc.monthly_total_max == 1199.0
    assert calc.setup_total_min == 0.0
    assert calc.setup_total_max == 0.0
    assert calc.estimated_first_month_min == 999.0
    assert calc.estimated_first_month_max == 1199.0


def test_setup_charges_calculation():
    """Verify setup charges are accumulated correctly."""
    # P19 (Cloud POS, setup 2500) + P09 (Backup failover, setup 1500)
    calc = pricing_engine.calculate_price(["P19", "P09"])
    expected_setup = 2500.0 + 1500.0
    assert calc.setup_total_min == expected_setup
    assert calc.setup_total_max == expected_setup
    # First month = monthly + setup
    assert calc.estimated_first_month_min == calc.monthly_total_min + expected_setup


def test_quantity_multiplier_per_site():
    """Verify per-site multiplier applies across multi-location profile."""
    profile_3_sites = BusinessProfile(
        business_type="Branch Clinic",
        num_sites=3,
        employee_count=10,
    )
    # P01: per site (999 * 3 = 2997 min)
    calc = pricing_engine.calculate_price(["P01"], profile=profile_3_sites)
    assert calc.product_breakdown[0].quantity == 3
    assert calc.monthly_total_min == 999.0 * 3
    assert calc.monthly_total_max == 1199.0 * 3


def test_quantity_multiplier_per_user_email():
    """Verify per-user multiplier applies to SaaS email licensing."""
    profile_5_users = BusinessProfile(
        business_type="CA Firm",
        employee_count=5,
        num_users=5,
    )
    # P16: Cloud Email per user (125 * 5 = 625 min)
    calc = pricing_engine.calculate_price(["P16"], profile=profile_5_users)
    assert calc.product_breakdown[0].quantity == 5
    assert calc.monthly_total_min == 125.0 * 5
    assert calc.monthly_total_max == 150.0 * 5


def test_quantity_override():
    """Verify explicit quantity override takes precedence."""
    calc = pricing_engine.calculate_price(["P07"], quantity_overrides={"P07": 4})
    # P07: Business Postpaid 299 * 4 = 1196
    assert calc.product_breakdown[0].quantity == 4
    assert calc.monthly_total_min == 299.0 * 4


def test_add_on_pricing_bundle():
    """Verify combined bundle with multiple add-ons."""
    # P01 (Fibre 100: 999) + P19 (POS: 599) + P07 (Mobile: 299)
    calc = pricing_engine.calculate_price(["P01", "P19", "P07"])
    assert calc.monthly_total_min == 999.0 + 599.0 + 299.0
    assert len(calc.product_breakdown) == 3
    assert len(calc.contract_details) == 3


def test_invalid_product_id_in_pricing():
    """Verify ValueError when calculating pricing for non-existent product."""
    with pytest.raises(ValueError, match="not found in catalogue"):
        pricing_engine.calculate_price(["P01", "P99_INVALID"])

