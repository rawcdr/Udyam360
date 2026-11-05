"""Unit tests for GeminiLLMService health check and initialization."""

import pytest
try:
    from backend.app.services.llm_service import GeminiLLMService
except ModuleNotFoundError:
    from app.services.llm_service import GeminiLLMService


def test_llm_service_health_check_with_key():
    """Verify health check reports healthy when API key is provided."""
    service = GeminiLLMService(api_key="mock_test_key_xyz", model_name="gemini-3.1-flash-lite")
    health = service.check_health()
    assert health["status"] == "HEALTHY"
    assert health["api_key_configured"] is True
    assert health["configured_model"] == "gemini-3.1-flash-lite"
    assert health["provider"] == "google-gemini"


def test_llm_service_health_check_without_key():
    """Verify health check reports degraded when API key is missing."""
    service = GeminiLLMService(api_key="", model_name="gemini-3.1-flash-lite")
    health = service.check_health()
    assert health["status"] == "DEGRADED"
    assert health["api_key_configured"] is False


def test_llm_service_get_client_raises_without_key():
    """Verify client initialization fails cleanly when no key is present."""
    service = GeminiLLMService(api_key="", model_name="gemini-3.1-flash-lite")
    with pytest.raises(ValueError, match="GEMINI_API_KEY is not set"):
        service.get_client()


def test_llm_service_generate_text_rejects_empty_prompt():
    """Verify generate_text validates input before calling client."""
    service = GeminiLLMService(api_key="mock_key", model_name="gemini-3.1-flash-lite")
    with pytest.raises(ValueError, match="Prompt content cannot be empty"):
        service.generate_text("")
