"""Unit tests for KYC consent capture, rejection, and withdrawal (Scenarios 18, 19)."""

from app.services.kyc_consent_service import KYCConsentService


def test_consent_record_granted():
    service = KYCConsentService()
    case_id = "KYC-TEST-001"

    rec = service.record_consent(case_id, consent_granted=True)
    assert rec.consent_granted is True
    assert rec.withdrawn is False
    assert service.is_consent_active(case_id) is True


def test_scenario_18_consent_declined():
    service = KYCConsentService()
    case_id = "KYC-TEST-002"

    rec = service.record_consent(case_id, consent_granted=False)
    assert rec.consent_granted is False
    assert service.is_consent_active(case_id) is False


def test_scenario_19_consent_withdrawal():
    service = KYCConsentService()
    case_id = "KYC-TEST-003"

    service.record_consent(case_id, consent_granted=True)
    assert service.is_consent_active(case_id) is True

    withdrawn_rec = service.withdraw_consent(case_id)
    assert withdrawn_rec.withdrawn is True
    assert withdrawn_rec.withdrawn_timestamp is not None
    assert service.is_consent_active(case_id) is False

