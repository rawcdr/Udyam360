"""PyTest fixtures and configuration.

Guarantees that test runs are deterministic, offline, and do not consume
live Gemini API quota during test suite execution.
"""

import pytest
from app.core.config import settings


@pytest.fixture(autouse=True)
def ensure_offline_unit_tests(monkeypatch):
    """Ensure automated test execution runs offline without consuming live Gemini quota."""
    # Use deterministic extractors and templates by default in unit tests
    monkeypatch.setattr(settings, "ADVISOR_ENABLED", False)

