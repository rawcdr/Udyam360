"""Unit tests for Conversation Management and Multi-Turn State."""

import pytest
from app.services.conversation_service import ConversationService
from app.schemas.advisor import ProfileExtractionResult, ExtractedProfileData


def test_create_and_retrieve_conversation():
    """Verify unique conversation ID generation and retrieval."""
    svc = ConversationService()
    c1 = svc.create_conversation()
    c2 = svc.create_conversation()

    assert c1.conversation_id != c2.conversation_id
    assert svc.get_conversation(c1.conversation_id) is not None
    assert svc.get_conversation(c2.conversation_id) is not None


def test_customer_correction_scenario_d():
    """Scenario D: User initially says 5 employees, then corrects to 3."""
    svc = ConversationService()
    c = svc.create_conversation()
    cid = c.conversation_id

    # Turn 1: 5 employees
    ext1 = ProfileExtractionResult(
        extracted_profile=ExtractedProfileData(business_type="Retail Shop", employee_count=5),
        fields_updated=["business_type", "employee_count"],
    )
    p1, _ = svc.merge_extracted_profile(cid, ext1)
    assert p1.employee_count == 5

    # Turn 2: Correction to 3 employees
    ext2 = ProfileExtractionResult(
        extracted_profile=ExtractedProfileData(employee_count=3),
        fields_updated=["employee_count"],
    )
    p2, updated = svc.merge_extracted_profile(cid, ext2)
    assert p2.employee_count == 3
    assert "employee_count" in updated
    # Earlier business type must be preserved!
    assert p2.business_type == "Retail Shop"


def test_customer_contradiction_location_scenario_e():
    """Scenario E: User updates location from Chennai to Coimbatore."""
    svc = ConversationService()
    c = svc.create_conversation()
    cid = c.conversation_id

    ext1 = ProfileExtractionResult(
        extracted_profile=ExtractedProfileData(business_type="Pharmacy", city="Chennai", city_tier=1),
        fields_updated=["business_type", "city", "city_tier"],
    )
    p1, _ = svc.merge_extracted_profile(cid, ext1)
    assert p1.city == "Chennai"
    assert p1.city_tier == 1

    # Follow-up: shop is in Coimbatore
    ext2 = ProfileExtractionResult(
        extracted_profile=ExtractedProfileData(city="Coimbatore", city_tier=2),
        fields_updated=["city", "city_tier"],
    )
    p2, updated = svc.merge_extracted_profile(cid, ext2)
    assert p2.city == "Coimbatore"
    assert p2.city_tier == 2
    assert "city" in updated


def test_conversation_isolation_scenario_j():
    """Scenario J: Two simultaneous conversations remain completely isolated."""
    svc = ConversationService()
    c1 = svc.create_conversation()
    c2 = svc.create_conversation()

    # Session 1: Pharmacy with ₹3,000 budget in Pune
    ext1 = ProfileExtractionResult(
        extracted_profile=ExtractedProfileData(
            business_type="Pharmacy", city="Pune", monthly_budget_inr=3000.0
        ),
        fields_updated=["business_type", "city", "monthly_budget_inr"],
    )
    svc.merge_extracted_profile(c1.conversation_id, ext1)
    svc.add_user_message(c1.conversation_id, "I run a pharmacy in Pune.")

    # Session 2: CA Firm with ₹8,000 budget in Delhi
    ext2 = ProfileExtractionResult(
        extracted_profile=ExtractedProfileData(
            business_type="CA Firm", city="Delhi", monthly_budget_inr=8000.0
        ),
        fields_updated=["business_type", "city", "monthly_budget_inr"],
    )
    svc.merge_extracted_profile(c2.conversation_id, ext2)
    svc.add_user_message(c2.conversation_id, "I run a CA firm in Delhi.")

    state1 = svc.get_conversation(c1.conversation_id)
    state2 = svc.get_conversation(c2.conversation_id)

    # Verify session 1 data did not bleed into session 2
    assert state1.profile.business_type == "Pharmacy"
    assert state1.profile.city == "Pune"
    assert state1.profile.monthly_budget_inr == 3000.0

    assert state2.profile.business_type == "CA Firm"
    assert state2.profile.city == "Delhi"
    assert state2.profile.monthly_budget_inr == 8000.0

    assert "CA firm" not in [m.content for m in state1.history]
    assert "pharmacy" not in [m.content for m in state2.history]


def test_conversation_reset():
    """Verify conversation reset clears history and profile."""
    svc = ConversationService()
    c = svc.create_conversation()
    cid = c.conversation_id

    svc.add_user_message(cid, "Hello")
    svc.merge_extracted_profile(
        cid,
        ProfileExtractionResult(
            extracted_profile=ExtractedProfileData(business_type="Clinic"),
            fields_updated=["business_type"],
        ),
    )

    reset_ok = svc.reset_conversation(cid)
    assert reset_ok is True

    state = svc.get_conversation(cid)
    assert state.profile.business_type is None
    assert len(state.history) == 0
    assert state.turn_count == 0

