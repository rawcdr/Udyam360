"""Integration tests for KYC FastAPI REST API endpoints."""

import io
from PIL import Image
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.conversation_service import conversation_service


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def active_session():
    state = conversation_service.create_conversation()
    sess_id = state.conversation_id
    conv = conversation_service.get_conversation(sess_id)
    conv.profile.business_name = "Zenith Diagnostics"
    conv.profile.business_type = "Diagnostic Clinic"
    conv.profile.business_segment = "prof"
    conv.profile.employee_count = 5
    conv.profile.num_sites = 1
    conv.profile.city = "Nagpur"
    conv.profile.city_tier = 2
    conv.profile.has_gstin = True
    conv.profile.monthly_budget_inr = 6000.0
    return sess_id


def make_dummy_png():
    img = Image.new("RGB", (150, 150), color=(220, 220, 220))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_kyc_api_full_lifecycle(client, active_session):
    # 1. Create Case
    create_payload = {
        "advisor_session_id": active_session,
        "selected_product_ids": ["P01", "P16"],
        "quote_reference": "Q-TEST1234"
    }
    res = client.post("/api/v1/kyc/cases", json=create_payload)
    assert res.status_code == 201
    case_data = res.json()
    case_id = case_data["kyc_case_id"]
    token = case_data.get("session_token") or res.headers.get("x-session-token")
    headers = {"X-Session-Token": token}
    assert case_data["advisor_session_id"] == active_session

    # 2. Get Case (authenticated)
    res_get = client.get(f"/api/v1/kyc/cases/{case_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["kyc_case_id"] == case_id

    # 3. Record Consent (authenticated)
    consent_payload = {"consent_granted": True, "consent_version": "v1.0-2026"}
    res_consent = client.post(f"/api/v1/kyc/cases/{case_id}/consent", json=consent_payload, headers=headers)
    assert res_consent.status_code == 200
    assert res_consent.json()["consent_granted"] is True

    # 4. Upload Document (authenticated & consented)
    png_bytes = make_dummy_png()
    files = {"file": ("address_proof.png", png_bytes, "image/png")}
    data = {"document_type": "ADDRESS_PROOF"}
    res_upload = client.post(f"/api/v1/kyc/cases/{case_id}/documents", data=data, files=files, headers=headers)
    assert res_upload.status_code == 201
    doc_meta = res_upload.json()
    assert doc_meta["document_type"] == "ADDRESS_PROOF"

    # 5. List Documents (authenticated)
    res_list = client.get(f"/api/v1/kyc/cases/{case_id}/documents", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 6. Check Status (authenticated)
    res_status = client.get(f"/api/v1/kyc/cases/{case_id}/status", headers=headers)
    assert res_status.status_code == 200
    assert res_status.json()["consent_recorded"] is True

    # 7. Delete Case (authenticated)
    res_del = client.delete(f"/api/v1/kyc/cases/{case_id}", headers=headers)
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "deleted"

    # Verify not found after deletion
    res_after = client.get(f"/api/v1/kyc/cases/{case_id}", headers=headers)
    assert res_after.status_code == 404
