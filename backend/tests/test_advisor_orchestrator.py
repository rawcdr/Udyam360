"""Unit tests for Advisor Orchestrator and End-to-End Dialogue Flows."""

import pytest
from app.schemas.advisor import AdvisorMessageRequest
from app.services.advisor_orchestrator import AdvisorOrchestrator


def test_scenario_a_pharmacy_end_to_end():
    """Scenario A: Full flow for pharmacy in Chennai with 3 employees, 1 shop, UPI POS, CCTV, budget ₹3,000."""
    orchestrator = AdvisorOrchestrator()
    start_res = orchestrator.start_conversation()
    cid = start_res.conversation_id
    assert cid.startswith("conv_")

    message = (
        "I run a small pharmacy in Chennai. I have three employees and one shop. "
        "I need internet for UPI payments, billing software and CCTV. My monthly budget is ₹3,000."
    )
    req = AdvisorMessageRequest(conversation_id=cid, message=message)
    resp = orchestrator.process_message(req)

    assert resp.processing_status == "SUCCESS"
    assert resp.recommendations_available is True
    assert resp.recommendations is not None

    # Verify extracted profile
    prof = resp.extracted_profile
    assert prof.business_type == "Pharmacy"
    assert prof.employee_count == 3
    assert prof.num_sites == 1
    assert prof.city == "Chennai"
    assert prof.city_tier == 1
    assert prof.monthly_budget_inr == 3000.0

    # Verify recommendations reflect verified backend pricing
    recs = resp.recommendations
    assert recs.essential_bundle is not None
    assert recs.growth_bundle is not None
    assert recs.essential_bundle.pricing.monthly_total_min > 0
    # Must include POS (P19) or CCTV (P23) in growth
    growth_ids = recs.growth_bundle.product_ids
    assert "P19" in growth_ids or "P23" in growth_ids

    # Assistant message must ground in pricing
    assert "₹" in resp.assistant_message


def test_scenario_b_ca_practice_end_to_end():
    """Scenario B: CA practice in Delhi with 5 employees, email, backup, security, budget ₹5,000.
    
    Verifies that budget status accurately indicates PARTIALLY_WITHIN_BUDGET.
    """
    orchestrator = AdvisorOrchestrator()
    start_res = orchestrator.start_conversation()
    cid = start_res.conversation_id

    message = (
        "I run a CA practice in Delhi with five employees. "
        "I need business email, secure internet, cloud backup and endpoint protection. "
        "My budget is ₹5,000 per month."
    )
    req = AdvisorMessageRequest(conversation_id=cid, message=message)
    resp = orchestrator.process_message(req)

    assert resp.processing_status == "SUCCESS"
    assert resp.recommendations_available is True
    assert resp.recommendations is not None

    prof = resp.extracted_profile
    assert prof.business_type == "CA Practice"
    assert prof.employee_count == 5
    assert prof.city == "Delhi"
    assert prof.monthly_budget_inr == 5000.0

    growth = resp.recommendations.growth_bundle
    assert growth is not None
    # Verify budget status reflects that upper range exceeds budget
    assert growth.budget_status == "PARTIALLY_WITHIN_BUDGET"
    assert growth.max_budget_gap_inr > 0


def test_scenario_c_incomplete_information_follow_up():
    """Scenario C: 'I own a small shop' triggers follow-up rather than premature recommendation."""
    orchestrator = AdvisorOrchestrator()
    start_res = orchestrator.start_conversation()
    cid = start_res.conversation_id

    req = AdvisorMessageRequest(conversation_id=cid, message="I own a small shop.")
    resp = orchestrator.process_message(req)

    assert resp.processing_status == "SUCCESS"
    # Should NOT have returned recommendations yet
    assert resp.recommendations_available is False
    assert resp.recommendations is None

    # Should have identified missing fields (location, headcount)
    assert "city" in resp.missing_fields or "employee_count" in resp.missing_fields

    # Assistant message asks focused question
    assert "?" in resp.assistant_message

