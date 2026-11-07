"""Comprehensive Security Verification Tests for Udyam360 Remediations.

Verifies fixes for:
- VULN-01: Admin role default header bypass
- VULN-02: Systemic IDOR on customer orders
- VULN-03: Public order tracking PII exposure
- VULN-04: Unauthenticated KYC case deletion / DoS
- VULN-05: Systemic IDOR on KYC case details & documents
- VULN-06: Pre-consent document upload bypass
- VULN-07: Unauthorized order state machine tampering
- VULN-09: Encryption at rest for KYC document files
- VULN-10: Unauthenticated advisor reset & conversation hijacking
"""

import io
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.kyc_storage_service import kyc_storage_service

client = TestClient(app)


def make_test_png():
    img = Image.new("RGB", (60, 60), color=(10, 150, 80))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ============================================================
# 1. Admin Guard Tests (VULN-01)
# ============================================================

def test_admin_no_header_is_rejected():
    """Verify request with NO X-Admin-Role header is strictly rejected with 403."""
    res = client.get("/api/v1/admin/analytics/overview")
    assert res.status_code == 403
    assert "Access Denied" in res.json()["detail"]


def test_admin_invalid_role_is_rejected():
    """Verify request with invalid role is rejected with 403."""
    res = client.get(
        "/api/v1/admin/analytics/overview",
        headers={"X-Admin-Role": "UnauthorizedGuest"}
    )
    assert res.status_code == 403
    assert "Access Denied" in res.json()["detail"]


def test_admin_valid_role_is_accepted():
    """Verify request with valid ExecutiveAdmin role is accepted with 200."""
    res = client.get(
        "/api/v1/admin/analytics/overview",
        headers={"X-Admin-Role": "ExecutiveAdmin"}
    )
    assert res.status_code == 200
    assert "total_leads" in res.json()


# ============================================================
# 2. Advisor Session Separation & IDOR Tests (VULN-10)
# ============================================================

def test_advisor_cross_customer_idor_prevention():
    """Verify Customer B cannot access or reset Customer A's conversation."""
    # Customer A starts conversation
    res_a = client.post("/api/v1/advisor/start")
    conv_a = res_a.json()["conversation_id"]
    token_a = res_a.json()["session_token"]
    assert token_a is not None

    # Customer A adds message
    client.post(
        "/api/v1/advisor/message",
        json={"conversation_id": conv_a, "message": "My clinic is Apex Physio in Delhi."},
        headers={"X-Session-Token": token_a}
    )

    # Customer B starts conversation
    res_b = client.post("/api/v1/advisor/start")
    conv_b = res_b.json()["conversation_id"]
    token_b = res_b.json()["session_token"]

    # Test 1: Unauthenticated read of Conv A -> 401
    res_unauth = client.get(f"/api/v1/advisor/conversation/{conv_a}")
    assert res_unauth.status_code == 401

    # Test 2: Customer B tries to read Conv A -> 403
    res_idor_read = client.get(
        f"/api/v1/advisor/conversation/{conv_a}",
        headers={"X-Session-Token": token_b}
    )
    assert res_idor_read.status_code == 403
    assert "Access denied" in res_idor_read.json()["detail"]

    # Test 3: Customer B tries to reset Conv A -> 403
    res_idor_reset = client.post(
        f"/api/v1/advisor/reset/{conv_a}",
        headers={"X-Session-Token": token_b}
    )
    assert res_idor_reset.status_code == 403

    # Test 4: Customer A can read their own conversation -> 200
    res_own_read = client.get(
        f"/api/v1/advisor/conversation/{conv_a}",
        headers={"X-Session-Token": token_a}
    )
    assert res_own_read.status_code == 200
    assert res_own_read.json()["conversation_id"] == conv_a


# ============================================================
# 3. KYC Case Access Control & IDOR Tests (VULN-04, VULN-05)
# ============================================================

def test_kyc_cross_customer_idor_prevention():
    """Verify Customer B cannot read, modify, or delete Customer A's KYC case."""
    # Customer A creates case
    res_case_a = client.post(
        "/api/v1/kyc/cases",
        json={"advisor_session_id": "conv_cust_a", "selected_product_ids": ["P01"]}
    )
    case_a_id = res_case_a.json()["kyc_case_id"]
    token_a = res_case_a.json()["session_token"]

    # Customer B creates case
    res_case_b = client.post(
        "/api/v1/kyc/cases",
        json={"advisor_session_id": "conv_cust_b", "selected_product_ids": ["P02"]}
    )
    case_b_id = res_case_b.json()["kyc_case_id"]
    token_b = res_case_b.json()["session_token"]

    # Customer B attempts to read Case A -> 403
    res_read = client.get(
        f"/api/v1/kyc/cases/{case_a_id}",
        headers={"X-Session-Token": token_b}
    )
    assert res_read.status_code == 403

    # Customer B attempts to record consent on Case A -> 403
    res_consent = client.post(
        f"/api/v1/kyc/cases/{case_a_id}/consent",
        json={"consent_granted": True, "consent_version": "v1.0-2026"},
        headers={"X-Session-Token": token_b}
    )
    assert res_consent.status_code == 403

    # Customer B attempts to list documents for Case A -> 403
    res_docs = client.get(
        f"/api/v1/kyc/cases/{case_a_id}/documents",
        headers={"X-Session-Token": token_b}
    )
    assert res_docs.status_code == 403

    # Customer B attempts to delete Case A -> 403
    res_del = client.delete(
        f"/api/v1/kyc/cases/{case_a_id}",
        headers={"X-Session-Token": token_b}
    )
    assert res_del.status_code == 403

    # Customer A can read their own Case A -> 200
    res_own = client.get(
        f"/api/v1/kyc/cases/{case_a_id}",
        headers={"X-Session-Token": token_a}
    )
    assert res_own.status_code == 200
    assert res_own.json()["kyc_case_id"] == case_a_id


# ============================================================
# 4. KYC Consent Gate on Document Upload (VULN-06)
# ============================================================

def test_pre_consent_upload_is_strictly_blocked():
    """Verify document upload fails with 403 prior to explicit DPDP consent."""
    res_case = client.post(
        "/api/v1/kyc/cases",
        json={"advisor_session_id": "conv_consent_test", "selected_product_ids": ["P01"]}
    )
    case_id = res_case.json()["kyc_case_id"]
    token = res_case.json()["session_token"]
    headers = {"X-Session-Token": token}

    png_bytes = make_test_png()
    files = {"file": ("test_doc.png", png_bytes, "image/png")}
    data = {"document_type": "UDYAM_CERTIFICATE"}

    # Attempt upload BEFORE consent -> Must return 403
    res_blocked = client.post(
        f"/api/v1/kyc/cases/{case_id}/documents",
        data=data,
        files=files,
        headers=headers
    )
    assert res_blocked.status_code == 403
    assert "consent has not been granted" in res_blocked.json()["detail"]

    # Record consent
    client.post(
        f"/api/v1/kyc/cases/{case_id}/consent",
        json={"consent_granted": True, "consent_version": "v1.0-2026"},
        headers=headers
    )

    # Attempt upload AFTER consent -> Must succeed with 201
    files = {"file": ("test_doc.png", png_bytes, "image/png")}
    res_ok = client.post(
        f"/api/v1/kyc/cases/{case_id}/documents",
        data=data,
        files=files,
        headers=headers
    )
    assert res_ok.status_code == 201
    assert res_ok.json()["document_type"] == "UDYAM_CERTIFICATE"


# ============================================================
# 5. Encryption at Rest Verification (VULN-09)
# ============================================================

def test_document_stored_with_fernet_encryption_at_rest():
    """Verify file stored on disk is encrypted ciphertext, but decrypted in memory."""
    res_case = client.post(
        "/api/v1/kyc/cases",
        json={"advisor_session_id": "conv_enc_test", "selected_product_ids": ["P01"]}
    )
    case_id = res_case.json()["kyc_case_id"]
    token = res_case.json()["session_token"]
    headers = {"X-Session-Token": token}

    client.post(
        f"/api/v1/kyc/cases/{case_id}/consent",
        json={"consent_granted": True, "consent_version": "v1.0-2026"},
        headers=headers
    )

    raw_png = make_test_png()
    files = {"file": ("confidential.png", raw_png, "image/png")}
    data = {"document_type": "GST_CERTIFICATE"}

    res_upload = client.post(
        f"/api/v1/kyc/cases/{case_id}/documents",
        data=data,
        files=files,
        headers=headers
    )
    assert res_upload.status_code == 201
    doc_id = res_upload.json()["document_id"]

    # 1. Read directly from the filesystem
    doc_path = kyc_storage_service.get_document_path(doc_id)
    assert doc_path is not None
    assert doc_path.exists()

    with open(doc_path, "rb") as f:
        disk_bytes = f.read()

    # Disk bytes MUST NOT equal plaintext PNG bytes (starts with Fernet header b"gAAAAA")
    assert disk_bytes != raw_png
    assert disk_bytes.startswith(b"gAAAAA")

    # 2. Read through storage service: returns decrypted plaintext
    decrypted_bytes = kyc_storage_service.read_document_bytes(doc_id)
    assert decrypted_bytes == raw_png


# ============================================================
# 6. Order IDOR & State Tampering Tests (VULN-02, VULN-07)
# ============================================================

def test_order_cross_customer_idor_and_tampering_prevention():
    """Verify Customer B cannot read or advance Customer A's order."""
    # Customer A creates order
    payload_a = {
        "quote_reference": "Q-SEC-001",
        "selected_product_ids": ["P01"],
        "bundle_tier": "Growth",
        "customer_info": {
            "business_name": "Alpha Solutions",
            "contact_name": "Aarav Sharma",
            "contact_phone": "9876543210",
            "contact_email": "aarav@alpha.example.com",
            "city": "Mumbai",
            "installation_address": "100 Marine Lines, Mumbai"
        },
        "pricing": {
            "monthly_recurring_charges": 1999.0,
            "one_time_charges": 0.0,
            "estimated_first_month": 1999.0,
        }
    }
    res_a = client.post("/api/v1/orders", json=payload_a)
    order_a = res_a.json()
    order_a_id = order_a["order_id"]
    token_a = order_a["session_token"]

    # Customer B creates order
    payload_b = dict(payload_a, quote_reference="Q-SEC-002")
    payload_b["customer_info"] = {"business_name": "Beta Corp", "city": "Delhi"}
    res_b = client.post("/api/v1/orders", json=payload_b)
    token_b = res_b.json()["session_token"]

    # Test 1: Customer B tries to read Order A -> 403
    res_idor_get = client.get(
        f"/api/v1/orders/{order_a_id}",
        headers={"X-Session-Token": token_b}
    )
    assert res_idor_get.status_code == 403

    # Test 2: Customer B tries to advance Order A state -> 403
    res_idor_adv = client.post(
        f"/api/v1/orders/{order_a_id}/advance",
        json={"target_state": "ORDER_PROCESSING"},
        headers={"X-Session-Token": token_b}
    )
    assert res_idor_adv.status_code == 403

    # Test 3: Customer A can read their own order -> 200
    res_own_get = client.get(
        f"/api/v1/orders/{order_a_id}",
        headers={"X-Session-Token": token_a}
    )
    assert res_own_get.status_code == 200
    assert res_own_get.json()["order_id"] == order_a_id


# ============================================================
# 7. Public Tracking PII Masking Tests (VULN-03)
# ============================================================

def test_public_order_tracking_masks_customer_pii():
    """Verify public tracking endpoint masks phone, email, and address for unauthenticated callers."""
    payload = {
        "quote_reference": "Q-TRACK-001",
        "selected_product_ids": ["P01"],
        "bundle_tier": "Essential",
        "customer_info": {
            "business_name": "Kavita Diagnostics",
            "contact_name": "Kavita Patel",
            "contact_phone": "9812345678",
            "contact_email": "kavita@diagnostics.example.com",
            "city": "Ahmedabad",
            "installation_address": "Suite 502, Silicon Square, SG Highway, Ahmedabad"
        },
        "pricing": {
            "monthly_recurring_charges": 1499.0,
            "one_time_charges": 0.0,
            "estimated_first_month": 1499.0,
        }
    }
    res = client.post("/api/v1/orders", json=payload)
    order_ref = res.json()["order_reference"]
    owner_token = res.json()["session_token"]

    # 1. Unauthenticated public tracking
    public_res = client.get(f"/api/v1/orders/track/{order_ref}")
    assert public_res.status_code == 200
    public_data = public_res.json()
    info = public_data["customer_info"]

    # Public response keeps business name and city
    assert info["business_name"] == "Kavita Diagnostics"
    assert info["city"] == "Ahmedabad"

    # Public response MASKS phone, email, and street address
    assert info["contact_phone"] == "******5678"
    assert "9812345678" not in public_res.text
    assert "@diagnostics.example.com" in info["contact_email"]
    assert "kavita@" not in info["contact_email"]
    assert "Silicon Square" not in public_res.text
    assert "SG Highway" not in public_res.text
    assert "Detailed street address protected" in info["installation_address"]

    # 2. Authenticated owner tracking returns unmasked details
    owner_res = client.get(
        f"/api/v1/orders/track/{order_ref}",
        headers={"X-Session-Token": owner_token}
    )
    assert owner_res.status_code == 200
    owner_info = owner_res.json()["customer_info"]
    assert owner_info["contact_phone"] == "9812345678"
    assert owner_info["contact_email"] == "kavita@diagnostics.example.com"
    assert "Silicon Square" in owner_info["installation_address"]


# ============================================================
# 8. Token Tampering & Invalidation Tests
# ============================================================

def test_tampered_and_invalid_tokens_rejected():
    """Verify malformed or forged tokens return 401 Unauthorized."""
    # Malformed token
    res_bad = client.get(
        "/api/v1/advisor/conversation/conv_12345",
        headers={"X-Session-Token": "garbage_token_value"}
    )
    assert res_bad.status_code == 401

    # Forged signature
    res_forged = client.get(
        "/api/v1/advisor/conversation/conv_12345",
        headers={"X-Session-Token": "sess_12345.1762500000.badbadbadbadbadbadbadbadbadbadba"}
    )
    assert res_forged.status_code == 401

