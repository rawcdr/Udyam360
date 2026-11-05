"""Unit tests for Natural Language Profile Extraction."""

import pytest
from app.schemas.business_profile import BusinessProfile
from app.services.profile_extraction_service import ProfileExtractionService, resolve_city_tier


def test_city_tier_resolution_known_cities():
    """Verify tier mapping for confirmed Indian cities."""
    assert resolve_city_tier("Delhi") == 1
    assert resolve_city_tier("Chennai") == 1
    assert resolve_city_tier("Bengaluru") == 1
    assert resolve_city_tier("Jaipur") == 2
    assert resolve_city_tier("Lucknow") == 2
    assert resolve_city_tier("Coimbatore") == 2
    # Unknown city should return None rather than guessing
    assert resolve_city_tier("UnknownHamletXYZ") is None


def test_fallback_extraction_pharmacy_scenario_a():
    """Scenario A: Test extraction of pharmacy in Chennai with 3 staff and ₹3,000 budget."""
    service = ProfileExtractionService()
    message = (
        "I run a small pharmacy in Chennai. I have three employees and one shop. "
        "I need internet for UPI payments, billing software and CCTV. My monthly budget is ₹3,000."
    )
    res = service._extract_with_fallback(message, existing_profile=None)
    ext = res.extracted_profile

    assert ext.business_type == "Pharmacy"
    assert ext.business_segment == "micro"
    assert ext.city == "Chennai"
    assert ext.city_tier == 1
    assert ext.employee_count == 3
    assert ext.num_sites == 1
    assert ext.monthly_budget_inr == 3000.0
    assert "pos" in ext.required_services or "cctv" in ext.required_services


def test_fallback_extraction_ca_practice_scenario_b():
    """Scenario B: Test extraction of CA practice in Delhi with 5 employees and ₹5,000 budget."""
    service = ProfileExtractionService()
    message = (
        "I run a CA practice in Delhi with five employees. "
        "I need business email, secure internet, cloud backup and endpoint protection. "
        "My budget is ₹5,000 per month."
    )
    res = service._extract_with_fallback(message, existing_profile=None)
    ext = res.extracted_profile

    assert ext.business_type == "CA Practice"
    assert ext.business_segment == "prof"
    assert ext.city == "Delhi"
    assert ext.city_tier == 1
    assert ext.employee_count == 5
    assert ext.monthly_budget_inr == 5000.0
    assert "email" in ext.required_services
    assert "backup" in ext.required_services
    assert "security" in ext.required_services


def test_incomplete_information_scenario_c():
    """Scenario C: 'I own a small shop' must not hallucinate employee count, location, or GSTIN."""
    service = ProfileExtractionService()
    message = "I own a small shop."
    res = service._extract_with_fallback(message, existing_profile=None)
    ext = res.extracted_profile

    assert ext.employee_count is None
    assert ext.city is None
    assert ext.city_tier is None
    assert ext.has_gstin is None
    assert ext.monthly_budget_inr is None


def test_gstin_positive_and_negative_phrasing():
    """Verify GSTIN extraction handles both affirmative and negative declarations."""
    service = ProfileExtractionService()

    res_yes = service._extract_with_fallback("We have GST registration for our clinic.", None)
    assert res_yes.extracted_profile.has_gstin is True

    res_no = service._extract_with_fallback("We do not have GST, just a small retail counter.", None)
    assert res_no.extracted_profile.has_gstin is False


def test_extract_with_gemini_structured_parsing():
    """Verify _extract_with_gemini accurately parses JSON response from mock Gemini client."""
    from unittest.mock import MagicMock
    from app.services.llm_service import GeminiLLMService

    mock_llm = MagicMock(spec=GeminiLLMService)
    mock_llm.api_key = "mock_key"
    mock_llm.model_name = "gemini-3.1-flash-lite"

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = (
        '{"business_type": "Pharmacy", "business_segment": "micro", "employee_count": 3, '
        '"num_sites": 1, "city": "Chennai", "city_tier": 1, "monthly_budget_inr": 3000.0, '
        '"required_services": ["pos", "cctv"]}'
    )
    mock_client.models.generate_content.return_value = mock_response
    mock_llm.get_client.return_value = mock_client

    service = ProfileExtractionService(llm_svc=mock_llm)
    res = service._extract_with_gemini("I run a pharmacy in Chennai", existing_profile=None)

    assert res is not None
    assert res.extracted_profile.business_type == "Pharmacy"
    assert res.extracted_profile.city == "Chennai"
    assert res.extracted_profile.city_tier == 1
    assert res.extracted_profile.employee_count == 3
    assert res.extracted_profile.monthly_budget_inr == 3000.0
    assert "pos" in res.extracted_profile.required_services
