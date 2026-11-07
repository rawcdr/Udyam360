import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

ADMIN_HEADERS = {"X-Admin-Role": "ExecutiveAdmin"}


def test_get_kyc_exceptions_requires_auth():
    resp = client.get("/api/v1/admin/kyc/exceptions")
    assert resp.status_code == 403


def test_get_kyc_exceptions_with_admin_role():
    resp = client.get("/api/v1/admin/kyc/exceptions", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    case_ids = [c["case_id"] for c in data]
    assert "KYC-EXP-9042" in case_ids


def test_get_kyc_exception_detail_success():
    resp = client.get("/api/v1/admin/kyc/exceptions/KYC-EXP-9042", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["case_id"] == "KYC-EXP-9042"
    assert detail["customer_name"] == "Rajesh Kumar Sharma"
    assert detail["risk_level"] == "LOW"
    assert len(detail["cross_checks"]) > 0
    assert "Sole Proprietorship" in detail["copilot_analysis"]


def test_get_kyc_exception_detail_not_found():
    resp = client.get("/api/v1/admin/kyc/exceptions/NON_EXISTENT", headers=ADMIN_HEADERS)
    assert resp.status_code == 404


def test_resolve_kyc_exception_approve():
    payload = {
        "action": "APPROVE",
        "notes": "Verified sole proprietorship trade name against GST REG-06 and municipal trade certificate.",
        "officer_name": "Senior Compliance Officer",
    }
    resp = client.post(
        "/api/v1/admin/kyc/exceptions/KYC-EXP-9042/resolve",
        headers=ADMIN_HEADERS,
        json=payload,
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["case_id"] == "KYC-EXP-9042"
    assert result["status"] == "APPROVED"
    assert result["action_taken"] == "APPROVE"
    assert result["reviewed_by"] == "Senior Compliance Officer"

    # Verify the detail reflects the approved state
    check_resp = client.get("/api/v1/admin/kyc/exceptions/KYC-EXP-9042", headers=ADMIN_HEADERS)
    assert check_resp.json()["status"] == "APPROVED"

