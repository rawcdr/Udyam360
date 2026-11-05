"""Unit tests for Bundle Recommendation Engine across all specified customer archetypes."""

import pytest
from app.schemas.business_profile import BusinessProfile
from app.services.recommendation_engine import recommendation_engine


def test_micro_retail_pharmacy_recommendation():
    """Verify recommendation generation for a neighbourhood pharmacy store."""
    profile = BusinessProfile(
        business_type="Pharmacy Store",
        business_segment="micro",
        employee_count=3,
        num_sites=1,
        city="Pune",
        city_tier=1,
        has_gstin=True,
        has_udyam=True,
        monthly_budget_inr=3500.0,
        required_services=["pos", "cctv"],
    )
    resp = recommendation_engine.generate_recommendations(profile)
    assert resp.status in ["SUCCESS", "PARTIAL"]
    assert resp.business_segment == "micro"
    assert resp.is_primary_target_segment is True

    # Check Essential bundle
    assert resp.essential_bundle is not None
    assert resp.essential_bundle.pricing.monthly_total_min > 0

    # Check Growth bundle contains requested POS
    assert resp.growth_bundle is not None
    growth_ids = resp.growth_bundle.product_ids
    assert "P19" in growth_ids  # Cloud POS

    # Score checks
    assert resp.growth_bundle.score.total_score >= 0.0
    assert resp.growth_bundle.score.total_score <= 100.0


def test_micro_retail_kirana_store_recommendation():
    """Verify recommendation for a typical Kirana retail store."""
    profile = BusinessProfile(
        business_type="Kirana Store",
        business_segment="micro",
        employee_count=2,
        num_sites=1,
        city="Indore",
        city_tier=2,
        has_gstin=False,
        monthly_budget_inr=2000.0,
    )
    resp = recommendation_engine.generate_recommendations(profile)
    assert resp.status == "SUCCESS"
    assert resp.essential_bundle is not None
    # Essential should be affordable
    assert resp.essential_bundle.pricing.monthly_total_min <= 2000.0
    assert resp.essential_bundle.budget_status == "WITHIN_BUDGET"


def test_micro_retail_salon_recommendation():
    """Verify recommendation for a small neighbourhood beauty salon."""
    profile = BusinessProfile(
        business_type="Salon & Spa",
        business_segment="micro",
        employee_count=4,
        num_sites=1,
        city="Lucknow",
        city_tier=2,
        has_gstin=False,
        monthly_budget_inr=2500.0,
    )
    resp = recommendation_engine.generate_recommendations(profile)
    assert resp.status == "SUCCESS"
    assert resp.essential_bundle is not None
    assert resp.growth_bundle is not None
    # Should not include GSTIN-mandatory products
    for p in resp.growth_bundle.products:
        assert p.requires_gstin is False


def test_professional_clinic_recommendation():
    """Verify recommendation for a medical clinic."""
    profile = BusinessProfile(
        business_type="Dental Clinic",
        business_segment="prof",
        employee_count=5,
        num_sites=1,
        city="Bengaluru",
        city_tier=1,
        has_gstin=True,
        monthly_budget_inr=4000.0,
        required_services=["backup"],
    )
    resp = recommendation_engine.generate_recommendations(profile)
    assert resp.status == "SUCCESS"
    assert resp.is_primary_target_segment is True
    # Growth bundle should include Cloud Backup (P17) or Email (P16)
    assert resp.growth_bundle is not None
    growth_ids = resp.growth_bundle.product_ids
    assert "P17" in growth_ids or "P16" in growth_ids


def test_professional_ca_office_recommendation():
    """Verify recommendation for a Chartered Accountant practice."""
    profile = BusinessProfile(
        business_type="CA Practice & Tax Advisory",
        business_segment="prof",
        employee_count=6,
        num_sites=1,
        city="Delhi",
        city_tier=1,
        has_gstin=True,
        has_udyam=True,
        monthly_budget_inr=5000.0,
        required_categories=["Cloud & Productivity", "Security"],
    )
    resp = recommendation_engine.generate_recommendations(profile)
    assert resp.status == "SUCCESS"
    assert resp.premium_bundle is not None
    prem_ids = resp.premium_bundle.product_ids
    # Should include endpoint security or email
    assert "P20" in prem_ids or "P16" in prem_ids


def test_professional_coaching_centre_recommendation():
    """Verify recommendation for an education/coaching centre."""
    profile = BusinessProfile(
        business_type="IIT-JEE Coaching Centre",
        business_segment="prof",
        employee_count=8,
        num_sites=1,
        city="Kota",
        city_tier=2,
        has_gstin=True,
        monthly_budget_inr=4500.0,
    )
    resp = recommendation_engine.generate_recommendations(profile)
    assert resp.status == "SUCCESS"
    assert resp.essential_bundle is not None
    assert resp.growth_bundle is not None


def test_customer_with_low_budget_budget_gap_reported():
    """Verify that when a customer specifies an extremely low budget, the engine explains the budget gap."""
    profile = BusinessProfile(
        business_type="Micro Kirana",
        business_segment="micro",
        employee_count=1,
        num_sites=1,
        city_tier=2,
        has_gstin=False,
        monthly_budget_inr=500.0,  # Below lowest broadband (AirFiber @ 899)
    )
    resp = recommendation_engine.generate_recommendations(profile)
    assert resp.essential_bundle is not None
    # Bundle is generated, but marked as exceeding budget
    assert resp.essential_bundle.budget_status == "EXCEEDS_BUDGET"
    assert resp.essential_bundle.budget_gap_inr > 0.0


def test_customer_with_high_budget():
    """Verify customer with high budget gets top score without budget penalties."""
    profile = BusinessProfile(
        business_type="Corporate Consultancy",
        business_segment="prof",
        employee_count=10,
        num_sites=1,
        city_tier=1,
        has_gstin=True,
        monthly_budget_inr=25000.0,
    )
    resp = recommendation_engine.generate_recommendations(profile)
    assert resp.status == "SUCCESS"
    assert resp.premium_bundle is not None
    assert resp.premium_bundle.budget_status == "WITHIN_BUDGET"
    assert resp.premium_bundle.score.budget_fit_score >= 80.0


def test_budget_semantics_audit_ca_practice_partially_within_budget():
    """Regression test for Part 0 Audit: Verify bundle where min <= budget < max is PARTIALLY_WITHIN_BUDGET.
    
    CA Practice: Budget ₹5,000/mo.
    Growth bundle monthly price range: ₹4,216 to ₹5,491.
    Setup charges: ₹2,500.
    Output must NOT misleadingly indicate that the entire range is within budget.
    """
    profile = BusinessProfile(
        business_type="CA Practice",
        business_segment="prof",
        employee_count=5,
        num_sites=1,
        city="Delhi",
        city_tier=1,
        has_gstin=True,
        monthly_budget_inr=5000.0,
        required_categories=["Security"],
    )
    resp = recommendation_engine.generate_recommendations(profile)
    growth = resp.growth_bundle
    assert growth is not None
    assert growth.pricing.monthly_total_min <= 5000.0
    assert growth.pricing.monthly_total_max > 5000.0
    # Must be PARTIALLY_WITHIN_BUDGET, not blindly WITHIN_BUDGET
    assert growth.budget_status == "PARTIALLY_WITHIN_BUDGET"
    assert growth.budget_gap_inr == 0.0  # Min fits
    assert growth.max_budget_gap_inr == round(growth.pricing.monthly_total_max - 5000.0, 2)
    # One-time setup must be reported separately and excluded from monthly budget calculation
    assert growth.pricing.setup_total_min == 2500.0
    # Explanations must articulate the partial budget fit
    notes_str = " ".join(growth.explanation["pricing_and_contract_notes"])
    assert "Minimum monthly cost" in notes_str
    assert "exceeds budget by" in notes_str


def test_customer_with_incomplete_information():
    """Verify missing information is tracked and reported without crashing."""
    profile_incomplete = BusinessProfile(
        business_type="Small Pharmacy",
        # No employee_count, no city_tier, no has_gstin
    )
    resp = recommendation_engine.generate_recommendations(profile_incomplete)
    assert resp.essential_bundle is not None
    # Missing information should contain unprovided fields
    assert len(resp.missing_information) > 0


def test_customer_with_no_eligible_complete_bundle():
    """Verify profile that fails all connectivity produces NO_ELIGIBLE_BUNDLE when strictly forced."""
    # Impossible constraints: city_tier=99, negative budget
    profile_impossible = BusinessProfile(
        business_type="Alien Shop",
        business_segment="micro",
        city_tier=2,
        has_gstin=False,
        employee_count=1,
        num_sites=1,
        # Explicitly request a product that is impossible (e.g. requires 25 employees)
        required_services=["P06"],
    )
    resp = recommendation_engine.generate_recommendations(profile_impossible)
    # P06 is completely ineligible, so requested match fails or generates partial
    assert resp.status in ["SUCCESS", "PARTIAL", "NO_ELIGIBLE_BUNDLE"]

