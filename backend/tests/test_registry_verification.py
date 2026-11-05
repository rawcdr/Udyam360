"""Unit tests for mock GSTIN and Udyam registry lookups (Scenarios 1, 2, 8, 9, 10, 11, 12, 22)."""

from pathlib import Path
import pytest
from app.services.registry_verification_service import RegistryVerificationService


@pytest.fixture
def registry_service():
    return RegistryVerificationService()


def test_scenario_1_active_gstin_lookup(registry_service):
    # K02: Harmony Dental Care
    res = registry_service.verify_gstin("19EOGXH4115Y1ZL")
    assert res.found is True
    assert res.status == "Active"
    assert res.checks_passed is True
    assert "Harmony Dental Care" in str(res.registered_name)


def test_scenario_2_active_udyam_lookup(registry_service):
    # K02: Harmony Dental Care
    res = registry_service.verify_udyam("UDYAM-WB-00-5053330")
    assert res.found is True
    assert res.checks_passed is True
    assert res.status in ("Micro", "Small", "Medium")
    assert "Harmony Dental Care" in str(res.registered_name)


def test_scenario_8_cancelled_gstin_lookup(registry_service):
    # K01: Vindhya Tours & Travels
    res = registry_service.verify_gstin("37IHKXV5167L1ZS")
    assert res.found is True
    assert res.status == "Cancelled"
    assert res.checks_passed is False
    assert any("CANCELLED" in note for note in res.notes)


def test_scenario_9_suspended_gstin_lookup(registry_service):
    # Planted suspended status: 03ODMXS1407Q1ZD
    res = registry_service.verify_gstin("03ODMXS1407Q1ZD")
    assert res.found is True
    assert res.status == "Suspended"
    assert res.checks_passed is False
    assert any("SUSPENDED" in note for note in res.notes)


def test_scenario_10_registry_record_not_found(registry_service):
    res = registry_service.verify_gstin("99ZZZXS9999Z1Z9")
    assert res.found is False
    assert res.checks_passed is False
    assert any("not found" in note for note in res.notes)


def test_scenario_11_invalid_empty_gstin(registry_service):
    res = registry_service.verify_gstin("")
    assert res.found is False
    assert res.checks_passed is False


def test_scenario_12_invalid_empty_udyam(registry_service):
    res = registry_service.verify_udyam("")
    assert res.found is False
    assert res.checks_passed is False


def test_scenario_22_registry_file_unavailable():
    broken_service = RegistryVerificationService(
        gstin_path=Path("non_existent_gst.csv"),
        udyam_path=Path("non_existent_udyam.csv")
    )
    res = broken_service.verify_gstin("19EOGXH4115Y1ZL")
    assert res.found is False
    assert res.checks_passed is False
    assert any("Registry technical error" in note for note in res.notes)
