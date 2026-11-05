"""Unit tests for Product Eligibility and Dependency Engine."""

import pytest
from app.schemas.business_profile import BusinessProfile
from app.schemas.eligibility import EligibilityStatus
from app.services.catalogue_service import catalogue_service
from app.services.eligibility_engine import EligibilityEngine, eligibility_engine


def test_valid_customer_profile_broadband_eligibility():
    """Verify standard Micro Retail profile is eligible for Biz Fibre 100."""
    profile = BusinessProfile(
        business_type="Kirana Store",
        business_segment="micro",
        employee_count=2,
        num_sites=1,
        city="Jaipur",
        city_tier=2,
        has_gstin=False,
    )
    p01 = catalogue_service.get_product_by_id("P01")
    res = eligibility_engine.evaluate_product(p01, profile)
    assert res.is_eligible is True
    assert res.eligibility_status == EligibilityStatus.ELIGIBLE


def test_gstin_required_product_with_and_without_gstin():
    """Verify product P14 (Business SMS 10k, requires GSTIN) passes with GSTIN and fails without."""
    p14 = catalogue_service.get_product_by_id("P14")
    assert p14.requires_gstin is True

    # With GSTIN -> Eligible
    profile_with_gst = BusinessProfile(
        business_type="CA Office",
        employee_count=5,
        num_sites=1,
        city_tier=1,
        has_gstin=True,
    )
    res_with = eligibility_engine.evaluate_product(p14, profile_with_gst)
    assert res_with.is_eligible is True

    # Without GSTIN -> Ineligible
    profile_no_gst = BusinessProfile(
        business_type="Small Salon",
        employee_count=2,
        num_sites=1,
        city_tier=2,
        has_gstin=False,
    )
    res_without = eligibility_engine.evaluate_product(p14, profile_no_gst)
    assert res_without.is_eligible is False
    assert res_without.eligibility_status == EligibilityStatus.INELIGIBLE
    assert any("GSTIN" in r for r in res_without.reasons)


def test_insufficient_employee_count():
    """Verify product P06 (Internet Leased Line 100, requires 25 employees) fails for 5 employees."""
    p06 = catalogue_service.get_product_by_id("P06")
    profile = BusinessProfile(
        business_type="Small Office",
        employee_count=5,
        num_sites=1,
        city_tier=1,
        has_gstin=True,
    )
    res = eligibility_engine.evaluate_product(p06, profile)
    assert res.is_eligible is False
    assert res.eligibility_status == EligibilityStatus.INELIGIBLE
    assert any("Requires minimum 25 employees" in r for r in res.reasons)


def test_insufficient_number_of_sites():
    """Verify product P10 (Managed SD-WAN, requires 3 sites) fails for single-site business."""
    p10 = catalogue_service.get_product_by_id("P10")
    profile = BusinessProfile(
        business_type="Retail Shop",
        employee_count=12,
        num_sites=1,
        city_tier=1,
        has_gstin=True,
    )
    res = eligibility_engine.evaluate_product(p10, profile)
    assert res.is_eligible is False
    assert res.eligibility_status == EligibilityStatus.INELIGIBLE
    assert any("Requires minimum 3 business sites" in r for r in res.reasons)


def test_city_tier_mismatch():
    """Verify product P03 (Biz Fibre 1G, available only in Tier 1) fails for Tier 2 location."""
    p03 = catalogue_service.get_product_by_id("P03")
    assert p03.available_city_tiers == [1]

    profile_tier2 = BusinessProfile(
        business_type="Diagnostic Clinic",
        employee_count=10,
        num_sites=1,
        city_tier=2,
        has_gstin=True,
    )
    res = eligibility_engine.evaluate_product(p03, profile_tier2)
    assert res.is_eligible is False
    assert res.eligibility_status == EligibilityStatus.INELIGIBLE
    assert any("Product only available in city tier(s) [1]" in r for r in res.reasons)


def test_missing_customer_information():
    """Verify missing headcount and GSTIN produces NEEDS_INFORMATION instead of auto-rejection."""
    p05 = catalogue_service.get_product_by_id("P05")  # requires 10 employees & GSTIN
    profile_partial = BusinessProfile(
        business_type="Growing Clinic",
        city_tier=1,
        # employee_count and has_gstin left unprovided
    )
    res = eligibility_engine.evaluate_product(p05, profile_partial)
    assert res.is_eligible is False
    assert res.eligibility_status == EligibilityStatus.NEEDS_INFORMATION
    assert "employee_count" in res.missing_information
    assert "has_gstin" in res.missing_information


def test_product_dependency_resolution():
    """Verify P23 (Cloud CCTV) automatically resolves its requirement for broadband."""
    profile = BusinessProfile(
        business_type="Pharmacy Store",
        business_segment="micro",
        employee_count=3,
        num_sites=1,
        city_tier=2,
        has_gstin=False,
    )
    # CCTV standalone requires broadband
    p23 = catalogue_service.get_product_by_id("P23")
    res = eligibility_engine.evaluate_product(p23, profile)
    assert res.eligibility_status == EligibilityStatus.DEPENDENCY_REQUIRED

    # Resolve dependencies for bundle containing P23
    resolved, notes = eligibility_engine.resolve_dependencies({"P23"}, profile)
    assert "P23" in resolved
    # Broadband prerequisite (P04 or P01) must have been injected
    assert any(dep in resolved for dep in ["P01", "P02", "P03", "P04", "P05", "P06"])
    assert len(notes) > 0


def test_invalid_dependency_detected(tmp_path):
    """Verify ValueError when a product references an unknown prerequisite ID."""
    bad_csv = tmp_path / "bad_deps.csv"
    bad_csv.write_text(
        "product_id,category,product_name,description,unit,price_min_inr_per_month,price_max_inr_per_month,one_time_setup_inr,min_contract_months,available_city_tiers,min_employees,min_sites,requires_gstin,requires_one_of,typical_install_days,target_segments\n"
        "P01,Connectivity,Biz Fibre 100,Desc,per site,999,1199,0,12,1;2,1,1,N,NON_EXISTENT_P99,5,micro\n"
    )
    from app.services.catalogue_service import CatalogueService
    with pytest.raises(ValueError, match="requires non-existent product ID"):
        CatalogueService(csv_path=bad_csv)


def test_circular_dependency_protection(tmp_path):
    """Verify ValueError when a product attempts to depend directly on itself."""
    bad_csv = tmp_path / "self_dep.csv"
    bad_csv.write_text(
        "product_id,category,product_name,description,unit,price_min_inr_per_month,price_max_inr_per_month,one_time_setup_inr,min_contract_months,available_city_tiers,min_employees,min_sites,requires_gstin,requires_one_of,typical_install_days,target_segments\n"
        "P01,Connectivity,Biz Fibre 100,Desc,per site,999,1199,0,12,1;2,1,1,N,P01,5,micro\n"
    )
    from app.services.catalogue_service import CatalogueService
    with pytest.raises(ValueError, match="cannot depend on itself"):
        CatalogueService(csv_path=bad_csv)

